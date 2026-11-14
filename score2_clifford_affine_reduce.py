#!/usr/bin/env python3
"""Exact X/CX/SWAP block resynthesis before non-Clifford decomposition.

Every accepted block has the identical affine map on arbitrary inputs. HMR,
phase operations, condition changes and nonlinear gates remain barriers.
Three Gaussian-elimination orders and the transposed linear map are compared;
a rewrite is accepted only when the total elementary gate count decreases.
This is the affine Clifford fragment, not unrestricted ZX circuit extraction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

ALLOWED = {'X','CX','SWAP'}


def expand_swaps_for_checker(circuit):
    """The existing independent truth-table checker supports CX but not SWAP."""
    import kickmix as km
    lines=[]
    for line in str(circuit).splitlines():
        p=parse(line)
        if p is not None and p[0]=='SWAP':
            a,b=p[1]
            lines.extend((f'CX q{a} q{b}',f'CX q{b} q{a}',f'CX q{a} q{b}'))
        else:lines.append(line)
    return km.Circuit('\n'.join(lines)+'\n')


def parse(line):
    w=line.split()
    if not w or w[0] not in ALLOWED or 'if' in w:
        return None
    return w[0],tuple(int(v[1:]) for v in w[1:])


def affine(ops, wires):
    n=len(wires);idx={q:i for i,q in enumerate(wires)}
    rows=[1<<i for i in range(n)]
    for op,qubits in ops:
        q=[idx[x] for x in qubits]
        if op=='X':rows[q[0]]^=1<<n
        elif op=='CX':rows[q[1]]^=rows[q[0]]
        else:rows[q[0]],rows[q[1]]=rows[q[1]],rows[q[0]]
    return rows


def eliminate(matrix, order):
    rows=matrix.copy();n=len(rows);gates=[]
    for col in order:
        remaining=[r for r in order if r not in order[:order.index(col)]]
        pivot=min((r for r in remaining if rows[r]>>col&1),key=lambda r:(rows[r].bit_count(),r!=col))
        if pivot!=col:
            rows[pivot],rows[col]=rows[col],rows[pivot]
            gates.append(('SWAP',(pivot,col)))
        for r in range(n):
            if r!=col and rows[r]>>col&1:
                rows[r]^=rows[col];gates.append(('CX',(col,r)))
    assert rows==[1<<i for i in range(n)]
    return list(reversed(gates))


def optimize(ops):
    wires=sorted({q for _,qs in ops for q in qs});n=len(wires)
    original=affine(ops,wires);mask=(1<<n)-1
    matrix=[r&mask for r in original]
    translations=[('X',(i,)) for i,r in enumerate(original) if r>>n&1]
    best=ops
    orders=[list(range(n)),list(reversed(range(n))),sorted(range(n),key=lambda i:matrix[i].bit_count())]
    transposed=[sum(((matrix[r]>>c)&1)<<r for r in range(n)) for c in range(n)]
    for transpose,a in [(False,matrix),(True,transposed)]:
        for order in orders:
            plan=eliminate(a,order)
            if transpose:
                plan=[(op,tuple(reversed(qs)) if op=='CX' else qs) for op,qs in reversed(plan)]
            plan+=translations
            if len(plan)>=len(best):continue
            mapped=[(op,tuple(wires[q] for q in qs)) for op,qs in plan]
            if affine(mapped,wires)!=original:
                raise AssertionError('Affine-map certificate failed')
            best=mapped
    return best,n


def reduce_lines(lines):
    rewritten=[];pending=[];changes=[];block_start=0;counts=Counter()
    def flush():
        nonlocal pending
        if not pending:return
        ops=[parse(s) for s in pending]
        counts['affine_blocks']+=1
        if len(ops)<6:
            rewritten.extend(pending);pending=[];return
        candidate,n=optimize(ops)
        counts['certified_blocks']+=1
        if len(candidate)<len(ops):
            lines2=[' '.join([name]+[f'q{q}' for q in qs]) for name,qs in candidate]
            rewritten.extend(lines2)
            changes.append({'source_start_zero_based':block_start,'old_gates':len(ops),'new_gates':len(candidate),'wires':n})
        else:rewritten.extend(pending)
        pending=[]
    for i,line in enumerate(lines):
        if parse(line) is not None:
            if not pending:block_start=i
            pending.append(line)
        else:flush();rewritten.append(line)
    flush()
    return rewritten,changes,dict(counts)


def checked_angle_words(path):
    """Validate the complete claimed domain before any uint64 conversion."""
    import numpy as np
    with np.load(path, allow_pickle=False) as data:
        raw = np.array(data['angle_words'])
    if raw.shape != (1220, 75):
        raise ValueError(f'Expected complete (1220, 75) angle table, got {raw.shape}')
    if not np.issubdtype(raw.dtype, np.integer):
        raise ValueError(f'Expected integer angle words, got {raw.dtype}')
    if np.any(raw < 0) or np.any(raw > 255):
        raise ValueError('Angle words must be in the inclusive 8-bit range 0..255')
    return raw.astype(np.uint64)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--loaders',type=Path)
    p.add_argument('--kmx',type=Path)
    p.add_argument('--table',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    start=time.monotonic();report={'status':'RUNNING','blocks':[],'scope':'Exact arbitrary-input affine maps; all non-affine operations retained',
                                 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                 'score_gain_claimed':False,'full_official_verification':False}
    paths=sorted(args.loaders.glob('angle_k_*.kmb')) if args.loaders else [args.kmx]
    if not paths:raise ValueError('No input circuits')
    import kickmix as km
    for source in paths:
        circuit=km.Circuit.from_file(source) if source.suffix=='.kmb' else km.Circuit(source.read_text())
        old=str(circuit).splitlines();new,changes,counts=reduce_lines(old)
        candidate=km.Circuit('\n'.join(new)+'\n')
        if candidate.num_qubits!=circuit.num_qubits:raise AssertionError('Layout changed')
        if candidate.operation_statistics().num_toffoli_like!=circuit.operation_statistics().num_toffoli_like:raise AssertionError('Non-Clifford cost changed')
        out=args.out/(source.stem+'.kmb');candidate.to_file(out,format='kmb')
        row={'file':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
             'source_operations':len(circuit),'candidate_operations':len(candidate),'removed_operations':len(circuit)-len(candidate),
             'qubits':circuit.num_qubits,'toffoli':int(candidate.operation_statistics().num_toffoli_like),
             'changed_blocks':changes,'block_counts':counts,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
        report['blocks'].append(row)
        print(json.dumps({k:v for k,v in row.items() if k!='changed_blocks'}),flush=True)
        (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.loaders and args.table:
        import numpy as np
        from chemistry_reachable_exact_proof import pack,prove_one
        words=checked_angle_words(args.table)
        report['verified_table_sha256']=hashlib.sha256(args.table.read_bytes()).hexdigest()
        report['verified_word_shape']=list(words.shape)
        addresses=np.arange(len(words),dtype=np.uint64);ab=[pack((addresses>>q)&1) for q in range(11)]
        zero=np.zeros((len(words),5),dtype=np.uint64);proofs=[]
        for k in range(15):
            c=km.Circuit.from_file(args.out/f'angle_k_{k}.kmb')
            previous=words[:,5*(k-1):5*k] if k else zero;current=words[:,5*k:5*(k+1)]
            for direction,incoming,want in [('forward',previous,current),('reverse',current,previous)]:
                proofs.append(prove_one(expand_swaps_for_checker(c),incoming,want,ab,f'k={k}/{direction}'))
        report['reachable_phase_proofs']=proofs
        report['status']='EXACT_ALL_BATCHES_AND_PHASE_PASS'
        (args.out/'submission.npz').write_bytes(args.table.read_bytes())
    else:report['status']='EXACT_AFFINE_BLOCKS_PASS'
    report['removed_operations']=sum(x['removed_operations'] for x in report['blocks'])
    report['seconds']=time.monotonic()-start
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'removed_operations':report['removed_operations'],'seconds':report['seconds']}),flush=True)


if __name__=='__main__':main()
