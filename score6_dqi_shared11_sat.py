#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fixed-first-factor exact SAT for simultaneous shared GF8 products.

The local symmetry tensor has dimensions 3 x 6 x 6 and rank-12 input.
For rank 11, nonsingular slice counting forces first-axis multiplicities
m_u = 1 + [u dot a0 = 1]; scalar autotopy reduces a0 to 1.
A timeout is not a rank lower bound. No circuit or submission is emitted.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time

DEPS=Path('/workspace/scratch/3815fb5fae06/score_invsqrt_solver_deps')
if DEPS.exists():sys.path.insert(0,str(DEPS))
import z3


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def coefficients(terms):
    out=[[[0]*6 for _ in range(6)] for _ in range(3)]
    for u,v,w in terms:
        assert 0<u<8 and 0<v<64 and 0<w<64
        for i in range(3):
            for j in range(6):
                if (u>>i&1) and (v>>j&1):
                    for k in range(6):out[i][j][k]^=w>>k&1
    return out

def gf2rank(rows):
    b={}
    for r in rows:
        while r:
            p=r.bit_length()-1
            if p in b:r^=b[p]
            else:b[p]=r;break
    return len(b)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=Path(__file__).with_name('symmetry_dqi_20261115_gf8_joint12_input.txt'))
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--timeout-seconds',type=float,default=300)
    ap.add_argument('--fix-first-v',action='store_true',help='Use the GL(2,8) centralizer symmetry to fix one v=1')
    args=ap.parse_args();start=time.monotonic()
    lines=args.input.read_text().splitlines();n,r=map(int,lines[0].split());assert n==6 and r==12
    terms=[tuple(map(int,line.split())) for line in lines[1:] if line.strip()];assert len(terms)==12
    tensor=coefficients(terms)
    slices=[]
    for a in range(1,8):
        rows=[sum((sum(tensor[i][j][k] for i in range(3) if a>>i&1)%2)<<k for k in range(6)) for j in range(6)]
        rank=gf2rank(rows);assert rank==6;slices.append(dict(a=a,rank=rank,rows=rows))
    us=[u for u in range(1,8) for _ in range(1+(u&1))];assert len(us)==11
    weights=[sum((u&a).bit_count()%2 for u in us) for a in range(1,8)];assert weights==[8,6,6,6,6,6,6]
    z3.set_param(proof=True)
    solver=z3.SolverFor('QF_BV');solver.set(timeout=max(1,round(1000*args.timeout_seconds)))
    vs=[z3.BitVec(f'v_{i}',6) for i in range(11)];ws=[z3.BitVec(f'w_{i}',6) for i in range(11)]
    for v,w in zip(vs,ws):solver.add(v!=0,w!=0)
    for i in range(10):
        if us[i]==us[i+1]:solver.add(z3.ULT(vs[i],vs[i+1]))
    if args.fix_first_v:solver.add(vs[0]==1)
    for a in range(3):
        for b in range(6):
            terms2=[z3.If(z3.Extract(b,b,vs[j])==1,ws[j],z3.BitVecVal(0,6)) for j in range(11) if us[j]>>a&1]
            expr=terms2[0]
            for t in terms2[1:]:expr=expr^t
            expected=sum(tensor[a][b][k]<<k for k in range(6));solver.add(expr==expected)
    smt=args.out.with_suffix('.smt2');smt.write_text(solver.to_smt2())
    result={'status':'RUNNING','input':str(args.input),'input_sha256':digest(args.input),'source_sha256':digest(__file__),
       'z3_version':z3.get_version_string(),'dimensions':[3,6,6],'rank_target':11,'initial_rank':12,'first_factors':us,
       'first_factor_weights':weights,'nonsingular_slices':slices,'nonzero_factors':True,'within_group_v_strict_order':True,
       'fix_first_v':args.fix_first_v,'timeout_seconds':args.timeout_seconds,'tensor_coefficients':108,'smt2_path':str(smt),'smt2_sha256':digest(smt)}
    args.out.write_text(json.dumps(result,indent=2)+'\n');print('SAT solver started, fixed u factors='+str(us),flush=True)
    check=solver.check();result['solver_result']=str(check);result['seconds']=time.monotonic()-start;result['statistics']=str(solver.statistics())
    if check==z3.sat:
        model=solver.model();found=[(u,model.eval(v,model_completion=True).as_long(),model.eval(w,model_completion=True).as_long()) for u,v,w in zip(us,vs,ws)]
        assert coefficients(found)==tensor
        def eval_terms(ts,a,b):
            y=0
            for u,v,w in ts:
                if (u&a).bit_count()%2 and (v&b).bit_count()%2:y^=w
            return y
        assert all(eval_terms(terms,a,b)==eval_terms(found,a,b) for a in range(8) for b in range(64))
        result.update(status='SAT_EXACT_RANK11_TENSOR',terms=found,all_108_coefficients_equal=True,all_512_input_pairs_equal=True)
    elif check==z3.unsat:
        proof=args.out.with_suffix('.proof.txt');proof.write_text(str(solver.proof())+'\n')
        result.update(status='UNSAT_FIXED_FACTOR_CASE',proof_path=str(proof),proof_sha256=digest(proof),proof_bytes=proof.stat().st_size,
                      scope='Fixed first-factor multiplicities only; unrestricted rank conclusion also requires the stated nonsingular-slice counting and field autotopy reduction.')
    else:result.update(status='UNKNOWN_NO_RANK_BOUND',reason_unknown=solver.reason_unknown())
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
