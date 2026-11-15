#!/usr/bin/env python3
"""Find direct paid gates replaced by exact reachable-domain Clifford operations."""
from pathlib import Path
import argparse, hashlib, json, re, random, sys
import numpy as np

BASE = Path('/workspace/scratch/7f542e06b7cf/gvqcc_repo')
sys.path.insert(0, str(BASE))
from score_invsqrt_retire import advance, affine_basis, solve

MAX_X = 3133452
SOURCE_SHA = '684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'
PAID = ('CCX','CCZ','CSWAP')

def columns(xs):
    packed = np.packbits(((xs[np.newaxis, :] >> np.arange(22, dtype=np.uint32)[:, np.newaxis]) & 1).astype('uint8'), axis=1, bitorder='little')
    return [int.from_bytes(b.tobytes(), 'little') for b in packed] + [0] * 24

def scan(lines, values, domain, only=None):
    branches = []
    hits = []
    checked = {}
    quantum_re = re.compile(r'\bq(\d+)\b')
    for lineno, line in enumerate(lines):
        op = line.split()[0]
        qs = tuple(map(int, quantum_re.findall(line)))
        if op == 'PUSH_CONDITION':
            branches.append(values[:])
        elif op == 'POP_CONDITION':
            assert branches.pop() == values, lineno
        elif op in ('CX','CCX','CSWAP','SWAP','X','HMR','R'):
            if ' if ' in line:
                raise ValueError(f'Unsupported inline guarded data operation: {line}')
            if op == 'R':
                assert not values[qs[0]], line
                continue
            if op == 'CCX' and (only is None or lineno in only):
                a,b,t = qs
                target = values[t] ^ (values[a] & values[b])
                forms = [()] + [(q,) for q in range(46) if q != t]
                terms = [domain] + [values[q] for (q,) in forms[1:]]
                checked['ccx_post'] = checked.get('ccx_post',0)+1
                coeff = solve(affine_basis(terms), target)
                if coeff is not None:
                    hits.append(dict(line=lineno, op='HMR_LINEAR', gate=line, depth=len(branches), terms=[forms[i] for i in range(len(forms)) if (coeff>>i)&1]))
            advance(op, qs, values, domain)
        elif op == 'CCZ' and (only is None or lineno in only):
            a,b,c = qs
            forms = [()] + [(q,) for q in range(46)] + [(q,r) for q in range(46) for r in range(q)]
            terms = [domain] + values + [values[q]&values[r] for q,r in forms[47:]]
            checked['ccz'] = checked.get('ccz',0)+1
            coeff = solve(affine_basis(terms), values[a]&values[b]&values[c])
            if coeff is not None:
                hits.append(dict(line=lineno, op='CCZ_QUADRATIC', gate=line, depth=len(branches), terms=[forms[i] for i in range(len(forms)) if (coeff>>i)&1]))
    assert not branches
    return hits,checked

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    ns=p.parse_args()
    import kickmix as km
    assert hashlib.sha256(ns.source.read_bytes()).hexdigest()==SOURCE_SHA
    c=km.Circuit.from_file(ns.source, format='kmb')
    lines=str(c).splitlines()
    rng=random.Random(9001)
    xs=np.array([1,2,3,MAX_X]+[rng.randint(1,MAX_X) for i in range(766)], dtype=np.uint32)
    hits, checked = scan(lines, columns(xs), (1<<len(xs))-1)
    print('sample',checked,hits, flush=True)
    valid=[]
    if hits:
        xs=np.arange(1,MAX_X+1,dtype=np.uint32)
        valid,_=scan(lines,columns(xs),(1<<len(xs))-1, only={v['line'] for v in hits})
        print('exact',valid,flush=True)
    if valid:
        fresh=max(int(s) for s in re.findall(r'\bb(\d+)\b','\n'.join(lines)))+1
        replacements={}
        for rec in valid:
            idx=rec['line']
            op=rec['op']
            line=lines[idx]
            nsuffix=line.split(' if ',1)
            suffix=' if '+nsuffix[1] if len(nsuffix)>1 else ''
            if op=='CCZ_QUADRATIC':
                replacements[idx]=[(('NEG' if not term else 'Z '+f'q{term[0]}' if len(term)==1 else f'CZ q{term[0]} q{term[1]}')+suffix) for term in rec['terms']]
            else:
                # HMR of pre-CCX t gives (-1)^(m*t); t=F XOR a*b.
                a,b,t=map(int,re.findall(r'\bq(\d+)\b',line))
                rep=[f'HMR q{t} b{fresh}', f'CZ q{a} q{b} if b{fresh}']
                for term in rec['terms']:
                    if not term:
                        rep += [f'NEG if b{fresh}',f'X q{t}']
                    else:
                        q,=term
                        rep += [f'Z q{q} if b{fresh}', f'CX q{q} q{t}']
                replacements[idx]=rep
        candidate_lines=[s for i,line in enumerate(lines) for s in replacements.get(i,[line])]
        c2=km.Circuit('\n'.join(candidate_lines)+'\n')
        assert c2.num_qubits==c.num_qubits
        c2.to_file(ns.out/'candidate.kmb',format='kmb')
        (ns.out/'candidate.kmx').write_text('\n'.join(candidate_lines)+'\n')
    (ns.out/'report.json').write_text(json.dumps(dict(source_sha=SOURCE_SHA, checked=checked, sample_hits=hits, certified=valid),indent=2)+'\n')

if __name__=='__main__':
    main()
