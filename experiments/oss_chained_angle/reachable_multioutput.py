#!/usr/bin/env python3
"""Reachability-certified, multi-output CCX resynthesis for ANGLE KMX.

This is a *postpass* on a real circuit, not a replacement for KickMix verification.
It permits non-injective source-state representations only on the specified
forward/reverse input domain, never as an irreversible quantum operation.

Rewrites only measurement-free windows whose CCX controls are not mutated data
outputs. All available controls are represented in one affine frame and all
CCX targets are represented as output directions. In that frame it searches:
- dependencies modulo the span of free live-wire affine corrections;
- two old products -> one newly factorized product;
- three old products -> two new products across w3=w1 XOR w2.

The last rule is genuinely multi-output: it can succeed even if the three old
products are independent modulo the reachable-domain affine span.

The result must still be checked with native KickMix, full HMR phase, Q, and
actual scorer before adoption. Source files are never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import hashlib
import json
import numpy as np


def insert(basis: dict, x: int, witness: int) -> bool:
    """Echelon basis of truth-bitsets with symbolic XOR support witness."""
    while x:
        p = x.bit_length() - 1
        if p not in basis:
            basis[p] = (x, witness)
            return True
        v, w = basis[p]
        x ^= v
        witness ^= w
    return False


def reduce(basis: dict, x: int) -> tuple[int, int]:
    witness = 0
    for p in sorted(basis, reverse=True):
        if x >> p & 1:
            v, w = basis[p]
            x ^= v
            witness ^= w
    return x, witness


def bits(x: int):
    while x:
        j = (x & -x).bit_length() - 1
        yield j
        x &= x - 1


def value(form: int, entry: list[int], ones: int) -> int:
    out = ones if form & 1 else 0
    for q in bits(form >> 1):
        out ^= entry[q]
    return out


def pack(vals) -> int:
    return sum(int(bool(v)) << i for i, v in enumerate(vals))


def build_initial(words: np.ndarray, k: int, nq: int, sel: list[int], word_regs: list[list[int]]) -> tuple[list[int], int]:
    """Both actual allowed directions, not arbitrary zero/random registers."""
    A = len(words)
    assert words.shape[1] == 75 and 0 <= k < 15 and len(sel) == 11
    if k:
        previous = words[:, 5*(k-1):5*k]
    else:
        previous = np.zeros((A, 5), dtype=np.uint8)
    current = words[:, 5*k:5*k+5]
    joined = np.concatenate([previous, current], axis=0)
    state = [0] * nq
    selrow = np.tile(np.arange(A, dtype=np.uint16), 2)
    for i, q in enumerate(sel):
        state[q] = pack((selrow >> i) & 1)
    for j, reg in enumerate(word_regs):
        for i, q in enumerate(reg):
            state[q] = pack((joined[:, j] >> i) & 1)
    return state, (1 << (2 * A)) - 1


def apply(state: list[int], gate: tuple, ones: int) -> None:
    op, qs, cond = gate
    if op == 'X' and cond is None:
        state[qs[0]] ^= ones
    elif op == 'CX' and cond is None:
        state[qs[1]] ^= state[qs[0]]
    elif op == 'CCX' and cond is None:
        state[qs[2]] ^= state[qs[0]] & state[qs[1]]
    elif op in {'R', 'HMR'} and cond is None:
        # Post-measurement computational qubit reset to 0. Phase tracked
        # separately by official checker after candidate generation.
        state[qs[0]] = 0
    elif op in {'CZ', 'Z', 'INFO_TAG'}:
        pass
    else:
        raise ValueError(f'unsupported state-transforming op: {gate}')


def parse_kmx(text: str):
    """Conservative line parser; preserves every original instruction verbatim."""
    lines = text.splitlines()
    instructions = []
    for i, line in enumerate(lines):
        t = line.split()
        if not t or t[0] in {'REGISTER', 'APPEND_TO_REGISTER'}:
            continue
        cond = t[t.index('if') + 1] if 'if' in t else None
        qs = tuple(int(z[1:]) for z in (t[:t.index('if')] if 'if' in t else t)[1:] if z.startswith('q'))
        instructions.append((i, (t[0], qs, cond)))
    return lines, instructions


def safe(gate, data: set[int]):
    name, q, condition = gate
    if condition is not None:
        return False
    if name == 'X':
        return True
    if name == 'CX':
        return not (q[0] in data and q[1] not in data)
    if name == 'CCX':
        return q[2] in data and q[0] not in data and q[1] not in data
    return False


def windows(instructions, data: set[int]):
    buf = []
    for idx, (_, op) in enumerate(instructions):
        if safe(op, data):
            buf.append(idx)
        else:
            if buf:
                if sum(instructions[i][1][0] == 'CCX' for i in buf) >= 2:
                    yield buf
                buf = []
    if buf and sum(instructions[i][1][0] == 'CCX' for i in buf) >= 2:
        yield buf


def extract(instructions, candidates, data: tuple[int, ...]):
    """Normalize controls in one entry frame and output targets in one exit frame."""
    dmap = {q: i for i, q in enumerate(data)}
    first = next(i for i in candidates if instructions[i][1][0] == 'CCX')
    last = next(i for i in reversed(candidates) if instructions[i][1][0] == 'CCX') + 1
    body = [instructions[i][1] for i in range(first, last)]
    maxq = max((max(q) for _, (_, q, _) in instructions if q), default=0) + 1
    pool = tuple(q for q in range(maxq) if q not in dmap)
    frame = [(1 << (q+1)) for q in range(maxq)]
    direction = {q: 1 << j for q, j in dmap.items()}
    targets = {}
    for i in range(last-1, first-1, -1):
        name, qs, cond = instructions[i][1]
        assert cond is None
        if name == 'CX' and qs[0] in dmap and qs[1] in dmap:
            direction[qs[0]] ^= direction[qs[1]]
        elif name == 'CCX':
            assert qs[2] in dmap
            targets[i] = direction[qs[2]]
    terms = []
    skeleton = []
    for i in range(first, last):
        name, qs, cond = instructions[i][1]
        assert cond is None
        if name == 'CCX':
            a, b, t = qs
            assert t in dmap and a not in dmap and b not in dmap
            terms.append((frame[a], frame[b], targets[i]))
        elif name == 'CX':
            a, b = qs
            assert not (a in dmap and b not in dmap)
            if b not in dmap:
                frame[b] ^= frame[a]
            skeleton.append(instructions[i][0])
        elif name == 'X':
            if qs[0] not in dmap:
                frame[qs[0]] ^= 1
            skeleton.append(instructions[i][0])
        else:
            raise AssertionError(name)
    return dict(first=first, last=last, terms=terms, pool=pool,
                skeleton=skeleton, frame=frame, data=data)


def free_basis(exit_values: list[int], pool: tuple[int, ...], ones: int) -> dict:
    B = {}
    insert(B, ones, 1 << len(pool))
    for j, q in enumerate(pool):
        insert(B, exit_values[q], 1 << j)
    return B


def nonlinear_terms_for_values(ex, entry_values: list[int], ones: int):
    return [(value(a, entry_values, ones) & value(b, entry_values, ones), w)
            for a,b,w in ex['terms']]


def collapse_dependencies(ex, terms, linears, entry_values, F, ones):
    """Arbitrary r-to-rank elimination with a multi-output fanout witness."""
    B = {}
    selected = []
    original_products = []
    for a, b, w in terms:
        p = value(a, entry_values, ones) & value(b, entry_values, ones)
        red, _ = reduce(F, p)
        r, support = reduce(B, red)
        if r:
            idx = len(selected)
            insert(B, red, 1 << idx)
            selected.append([a, b, w])
            original_products.append(p)
        else:
            correction = p
            for j in bits(support):
                selected[j][2] ^= w
                correction ^= original_products[j]
            _, witness = reduce(F, correction)
            assert reduce(F, correction)[0] == 0
            if witness:
                linears.append((witness, w))
    return [tuple(x) for x in selected if x[2]], linears


def candidates(terms, max_forms=96):
    count = Counter(v for a,b,_ in terms for v in (a,b))
    forms = [v for v,_ in count.most_common(max_forms) if v not in {0,1}]
    more = []
    # Each original product's two controls, and pairs sharing an output cone.
    for a,b,_ in terms:
        more.append(a ^ b)
    groups = {}
    for a,b,w in terms:
        groups.setdefault(w, []).extend((a,b))
    for g in groups.values():
        for i,x in enumerate(g[:12]):
            for y in g[i+1:12]:
                more.append(x ^ y)
    for z in more:
        if len(forms) >= max_forms:
            break
        if z not in {0,1} and z not in forms:
            forms.append(z)
    return forms


def product_dictionary(forms, entry, F, ones):
    """Only products implementable by existing affine pool forms are admitted."""
    fvals = [value(f, entry, ones) for f in forms]
    D = {}
    for i,a in enumerate(forms):
        for j in range(i+1,len(forms)):
            b = forms[j]
            if a ^ b == 1:  # constant product, use a free correction
                continue
            r,_ = reduce(F, fvals[i] & fvals[j])
            if r and r not in D:
                D[r] = (a,b)
    return D


def best_pair_or_triple(ex, terms, entry, F, D, ones):
    v = [(reduce(F, value(a,entry,ones)&value(b,entry,ones))[0],w)
         for a,b,w in terms]
    for i in range(len(terms)):
        for j in range(i+1,len(terms)):
            if v[i][1] == v[j][1] and (v[i][0]^v[j][0]) in D:
                a,b = D[v[i][0]^v[j][0]]
                old = value(terms[i][0],entry,ones)&value(terms[i][1],entry,ones)
                old ^= value(terms[j][0],entry,ones)&value(terms[j][1],entry,ones)
                correction = old ^ (value(a,entry,ones)&value(b,entry,ones))
                assert reduce(F,correction)[0]==0
                return (2, [i,j], [(a,b,v[i][1])],
                        [(reduce(F,correction)[1],v[i][1])])
    by_w = {}
    for i, (_,w) in enumerate(v):
        by_w.setdefault(w,[]).append(i)
    for i in range(len(v)):
        for j in range(i+1,len(v)):
            for k in by_w.get(v[i][1]^v[j][1],[]):
                if k in (i,j) or v[i][1]==v[j][1]:
                    continue
                A = v[i][0]^v[k][0]
                B = v[j][0]^v[k][0]
                if A not in D or B not in D:
                    continue
                aa,ab=D[A];ba,bb=D[B]
                p = [value(x,entry,ones)&value(y,entry,ones) for x,y,_ in terms]
                ca = p[i]^p[k]^(value(aa,entry,ones)&value(ab,entry,ones))
                cb = p[j]^p[k]^(value(ba,entry,ones)&value(bb,entry,ones))
                assert reduce(F,ca)[0]==reduce(F,cb)[0]==0
                return (3, [i,j,k],
                        [(aa,ab,v[i][1]),(ba,bb,v[j][1])],
                        [(reduce(F,ca)[1],v[i][1]),(reduce(F,cb)[1],v[j][1])])
    return None


def optimize_extracted(ex, entry_values: list[int], exit_values: list[int], ones: int):
    F = free_basis(exit_values, ex['pool'], ones)
    src = ex['terms']
    terms, linears = collapse_dependencies(ex, src, [], entry_values, F, ones)
    linear_removed = len(src)-len(terms)
    forms = candidates(terms)
    D = product_dictionary(forms, entry_values, F, ones)
    new_moves = []
    # Once a replacement is admitted, recompute exact quotient effects.
    for _ in range(12):
        move = best_pair_or_triple(ex,terms,entry_values,F,D,ones)
        if move is None:
            break
        _, indices, new, corrections = move
        terms = [t for i,t in enumerate(terms) if i not in indices] + new
        linears.extend((a,w) for a,w in corrections if a and w)
        terms,linears = collapse_dependencies(ex, terms, linears, entry_values,F,ones)
        new_moves.append({'old':len(indices),'new':len(new)})
    # Nothing gets emitted if the full reconstructed class is not cheaper.
    return dict(terms=terms,linears=linears,source=len(src),optimized=len(terms),
                zero_cost_linear_elimination=linear_removed,search_products=len(D),
                new_moves=new_moves,found_saving=len(src)-len(terms))


def abstract_expression(frame: list[int], query: int, pool: tuple[int, ...]) -> tuple[list[int],bool]:
    B={}
    for j,q in enumerate(pool):
        insert(B,frame[q],1<<j)
    insert(B,1,1<<len(pool))
    r,support=reduce(B,query)
    if r:
        raise ValueError('candidate control is not physically synthesizable')
    return [q for j,q in enumerate(pool) if support>>j&1], bool(support>>len(pool)&1)


def synthesize(ex, source_instructions, source_lines, plan):
    """Emit the same linear scaffold, followed by output updates and corrections."""
    if not plan['found_saving']:
        raise ValueError('no positive gain')
    frame=list(ex['frame'])
    data=ex['data']
    first, last=ex['first'],ex['last']
    body=[source_lines[source_instructions[i][0]] for i in range(first,last) if source_instructions[i][1][0]!='CCX']
    code=[]
    def make(form,exclude=None):
        wires,constant=abstract_expression(frame,form,ex['pool'])
        target=next((q for q in wires if q!=exclude),None)
        if target is None:
            raise ValueError('controls not independent')
        steps=[]
        for q in wires:
            if q!=target:
                steps.append(('CX',q,target))
                frame[target]^=frame[q]
        if constant:
            steps.append(('X',target))
            frame[target]^=1
        assert frame[target]==form
        for step in steps:
            code.append(' '.join([step[0]]+[f'q{x}' for x in step[1:]]))
        return target,steps
    def undo(steps):
        for step in steps[::-1]:
            if step[0]=='CX': frame[step[2]] ^= frame[step[1]]
            else: frame[step[1]] ^= 1
            code.append(' '.join([step[0]]+[f'q{x}' for x in step[1:]]))
    # All CCX in the exit frame, with output fanouts as free CNOTs.
    for a,b,w in plan['terms']:
        pa,sa=make(a)
        pb,sb=make(b,pa)
        outputs=[data[i] for i in bits(w)]
        if not outputs:
            undo(sb);undo(sa);continue
        pivot=outputs[0]
        for target in outputs[1:]:code.append(f'CX q{pivot} q{target}')
        code.append(f'CCX q{pa} q{pb} q{pivot}')
        for target in outputs[1:][::-1]:code.append(f'CX q{pivot} q{target}')
        undo(sb);undo(sa)
    # Linear correction witnesses refer to concrete exit physical pool wires.
    for lin,w in plan['linears']:
        outputs=[data[i] for i in bits(w)]
        for t in outputs:
            if lin>>len(ex['pool'])&1: code.append(f'X q{t}')
            for j in bits(lin&((1<<len(ex['pool']))-1)):
                code.append(f'CX q{ex["pool"][j]} q{t}')
    assert frame==ex['frame']
    return body+code


def optimize_text(text: str, state: list[int], ones: int, data: tuple[int, ...]):
    source_lines,instructions=parse_kmx(text)
    D=set(data)
    groups=list(windows(instructions,D))
    state=list(state)
    replacements=[];receipts=[]
    for group in groups:
        # Window need not contain header/footer unrelated to its nonlinear core.
        ex=extract(instructions,group,data)
        # Simulate from original entry by replaying original program until first CCX.
        # Avoid costly replays: each group is independent in this simulation.
        state_at_first=list(state)
        for i in range(0,ex['first']):
            apply(state_at_first,instructions[i][1],ones)
        state_at_end=list(state_at_first)
        for i in range(ex['first'],ex['last']):
            apply(state_at_end,instructions[i][1],ones)
        plan=optimize_extracted(ex,state_at_first,state_at_end,ones)
        receipt={k:plan[k] for k in ['source','optimized','found_saving','zero_cost_linear_elimination','search_products','new_moves']}
        receipt.update(first_operation=ex['first'],last_operation=ex['last']-1,
                       first_line=instructions[ex['first']][0],last_line=instructions[ex['last']-1][0],
                       full_stop=ex['last'])
        receipts.append(receipt)
        if plan['found_saving']>0:
            new_body=synthesize(ex,instructions,source_lines,plan)
            # Verify independent exact outputs and every scratch/control wire at boundary.
            normalized_state=list(state_at_first)
            for line in new_body:
                _,ops=parse_kmx(line)
                assert len(ops)==1
                apply(normalized_state,ops[0][1],ones)
            if normalized_state != state_at_end:
                receipt['status']='REJECTED_BOUNDARY_MISMATCH'
                continue
            receipt['status']='BOUNDARY_EXACT_PASS'
            replacements.append((receipt['first_line'],receipt['last_line']+1,new_body))
        else:
            receipt['status']='NO_SAVING_IN_CLASS'
    lines=list(source_lines)
    for first,last,body in reversed(replacements):
        lines[first:last]=body
    return '\n'.join(lines)+'\n',dict(windows=len(receipts),candidate_windows=len(replacements),
            source_ccx=sum(r['source'] for r in receipts),
            derived_ccx_saving=sum(r['found_saving'] for r in receipts if r['status']=='BOUNDARY_EXACT_PASS'),
            rows=receipts)


def optimize_file(kmx: Path, words: np.ndarray, k: int, output: Path, receipt: Path):
    # Uses upstream's known named register conventions; no extra quantum lines.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'third_party'/'manwithacat'))
    import kmsim
    ops,regs=kmsim.parse(kmx)
    names=kmsim.register_names(kmx)
    nq,_=kmsim.sizes(ops,regs)
    sel=regs[names['selection']]
    word_regs=[regs[names[f'word_{j}']] for j in range(5)]
    data=tuple(q for r in word_regs for q in r[:7])
    initial,ones=build_initial(words,k,nq,sel,word_regs)
    old=kmx.read_text()
    new,out=optimize_text(old,initial,ones,data)
    out.update(source_sha256=hashlib.sha256(old.encode()).hexdigest(),
               k=k,domain='1219 addresses x exact previous/current words',
               max_qubits=nq,source_modified=False,
               native_or_official_verifier_run=False)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(out,indent=2)+'\n')
    if out['candidate_windows']:
        assert new!=old
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(new)
        out['candidate_sha256']=hashlib.sha256(new.encode()).hexdigest()
        receipt.write_text(json.dumps(out,indent=2)+'\n')
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kmx',type=Path,required=True)
    p.add_argument('--words',type=Path,required=True,help='signed-gauge 1219x75 uint8/int64 numpy array')
    p.add_argument('--k',type=int,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    out=optimize_file(a.kmx,np.load(a.words),a.k,a.out,a.receipt)
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

if __name__=='__main__':main()