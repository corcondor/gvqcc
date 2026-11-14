#!/usr/bin/env python3
"""Exact reachable-table synthesis of the endpoint's joint v9/v10 restoration.

Uses a public Z3 wheel only as an optional SAT solver. Any returned program is
independently evaluated on the complete reachable table before export. The
table itself is extracted on every legal input of the exact current circuit.
"""
import argparse
from functools import reduce
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import score_invsqrt_retire as r

HERE=Path(__file__).parent
INPUTS=[18,9,34,36,30,32]
CAPTURE_BEFORE=7598
REPLACE_START=8432
REPLACE_END=8544


def extract():
    path=HERE/'invsqrt_structural_e46.kmx';lines,ops=r.instructions(path)
    assert lines[CAPTURE_BEFORE]=='HMR q20 b379'
    assert lines[REPLACE_START]=='CX q9 q19'
    assert lines[REPLACE_END]=='CX q20 q38'
    domain,vals=r.initial_values();stack=[];targets=None
    for i,(op,qs) in enumerate(ops):
        if i==CAPTURE_BEFORE:targets=[vals[19],vals[20]]
        if i==REPLACE_START:break
        if op=='PUSH_CONDITION':stack.append(vals[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==vals;vals=before
        else:r.advance(op,qs,vals,domain)
    assert not stack and vals[19]==vals[20]==0
    def unpack(v):
        return np.unpackbits(np.frombuffer(v.to_bytes((r.MAX_X+8)//8,'little'),dtype=np.uint8),bitorder='little')[:r.MAX_X+1]
    packed=np.zeros(r.MAX_X+1,dtype=np.uint16)
    for j,q in enumerate(INPUTS):packed|=unpack(vals[q]).astype(np.uint16)<<j
    for j,value in enumerate(targets):packed|=unpack(value).astype(np.uint16)<<(len(INPUTS)+j)
    rows=np.unique(packed[1:]).tolist();table={}
    for v in rows:
        inp=v&((1<<len(INPUTS))-1);out=v>>len(INPUTS)
        assert inp not in table,('target not determined by source inputs',inp)
        table[inp]=out
    report={'baseline_kmx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'all_legal_inputs':r.MAX_X,'input_qubits':INPUTS,'output_qubits':[19,20],
            'capture_before_line':CAPTURE_BEFORE+1,'replace_lines_inclusive':[REPLACE_START+1,REPLACE_END],
            'reachable_patterns':len(table),'rows':[[x,table[x]] for x in sorted(table)],
            'original_joint_AND_count':5}
    (HERE/'score_invsqrt_joint_table.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def synth(table,k,timeout,seed):
    try:
        import z3
    except ModuleNotFoundError:
        sys.path.insert(0,'/workspace/scratch/3815fb5fae06/score_invsqrt_solver_deps')
        import z3
    n=len(table['input_qubits']);rows=table['rows'];w=len(rows);mask=(1<<w)-1
    values=[z3.BitVecVal(sum(((x>>j)&1)<<i for i,(x,y) in enumerate(rows)),w) for j in range(n)]
    targets=[sum(((y>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(2)]
    solver=z3.SolverFor('QF_BV');solver.set(timeout=int(timeout*1000),random_seed=seed,max_memory=1024)
    selectors=[]
    def xor_selected(sels,vs):
        return reduce(lambda a,b:a^b,[z3.If(s,v,z3.BitVecVal(0,w)) for s,v in zip(sels,vs)],z3.BitVecVal(0,w))
    for g in range(k):
        a=[z3.Bool(f'a{g}_{j}') for j in range(n+g)];b=[z3.Bool(f'b{g}_{j}') for j in range(n+g)]
        ai=reduce(lambda x,y:x|y,[z3.If(t,z3.BitVecVal(1<<j,n+g),z3.BitVecVal(0,n+g)) for j,t in enumerate(a)])
        bi=reduce(lambda x,y:x|y,[z3.If(t,z3.BitVecVal(1<<j,n+g),z3.BitVecVal(0,n+g)) for j,t in enumerate(b)])
        # Three equivalent factor bases differ only by a previous linear form.
        solver.add(ai!=0,z3.ULT(ai,bi),z3.ULT(bi,ai^bi))
        v=z3.BitVec(f'g{g}',w);solver.add(v==xor_selected(a,values)&xor_selected(b,values))
        selectors.append((a,b));values.append(v)
    outputs=[]
    for j,target in enumerate(targets):
        out=[z3.Bool(f'o{j}_{i}') for i in range(n+k+1)]
        solver.add(xor_selected(out,values+[z3.BitVecVal(mask,w)])==z3.BitVecVal(target,w));outputs.append(out)
    # Every synthesized nonlinear signal must affect a later gate or an output.
    for g in range(k):
        uses=[out[n+g] for out in outputs]
        uses += [s[n+g] for pair in selectors[g+1:] for s in pair]
        solver.add(z3.Or(*uses))
    began=time.monotonic();status=solver.check();elapsed=time.monotonic()-began
    result={'k':k,'solver':'z3-solver 4.15.4.0','seed':seed,'timeout_seconds':timeout,
            'elapsed_seconds':elapsed,'status':str(status),'statistics':str(solver.statistics())}
    if status==z3.sat:
        model=solver.model()
        yes=lambda b:z3.is_true(model.eval(b,model_completion=True))
        gates=[{'left':[j for j,s in enumerate(a) if yes(s)],'right':[j for j,s in enumerate(b) if yes(s)]} for a,b in selectors]
        outs=[{'constant':int(yes(s[-1])),'terms':[j for j,t in enumerate(s[:-1]) if yes(t)]} for s in outputs]
        for x,y in rows:
            vs=[(x>>j)&1 for j in range(n)]
            for g in gates:vs.append((sum(vs[j] for j in g['left'])&1)&(sum(vs[j] for j in g['right'])&1))
            out=sum((o['constant']^(sum(vs[j] for j in o['terms'])&1))<<j for j,o in enumerate(outs))
            assert out==y
        result.update(gates=gates,outputs=outs,independent_table_check='PASS')
    elif status==z3.unknown:result['reason']=solver.reason_unknown()
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--k',type=int,default=4);ap.add_argument('--timeout',type=float,default=120)
    ap.add_argument('--seed',type=int,default=19);ap.add_argument('--reuse-table',action='store_true')
    ap.add_argument('--extract-only',action='store_true');args=ap.parse_args()
    table=json.loads((HERE/'score_invsqrt_joint_table.json').read_text()) if args.reuse_table else extract()
    print(json.dumps({k:v for k,v in table.items() if k!='rows'}),flush=True)
    if args.extract_only:return
    result=synth(table,args.k,args.timeout,args.seed)
    output={**table,**result};dest=HERE/f'score_invsqrt_joint_k{args.k}_seed{args.seed}.json';dest.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
