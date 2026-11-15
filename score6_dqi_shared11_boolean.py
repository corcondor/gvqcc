#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent Boolean/XOR encoding of shared GF8 rank11.

The tensor constants come from polynomial multiplication modulo x^3+x+1,
not from the rank12 decomposition or the BitVec model's tensor routine.
"""
from pathlib import Path
import argparse,functools,hashlib,json,resource,sys,time
DEPS=Path('/workspace/scratch/3815fb5fae06/score_invsqrt_solver_deps')
if DEPS.exists():sys.path.insert(0,str(DEPS))
import z3

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def mul(a,b):
    r=0
    while b:
        if b&1:r^=a
        b>>=1;a<<=1
        if a&8:a^=0xB
    return r

def oracle(a,b):return mul(a,b&7)|(mul(a,b>>3)<<3)
def parity(xs):
    assert xs
    return functools.reduce(z3.Xor,xs)
def bool_less(a,b):
    return z3.Or(*[z3.And(z3.Not(a[k]),b[k],*[a[h]==b[h] for h in range(k+1,6)]) for k in range(6)])
def exact_word(bits,value):return z3.And(*[b if value>>k&1 else z3.Not(b) for k,b in enumerate(bits)])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--timeout-seconds',type=float,default=60)
    args=ap.parse_args();start=time.monotonic();root=Path(__file__).parent
    source=root/'symmetry_dqi_20261115_gf8_joint12_input.txt'
    lines=source.read_text().splitlines();assert tuple(map(int,lines[0].split()))==(6,12)
    old=[tuple(map(int,l.split())) for l in lines[1:] if l.strip()]
    # Independent full input table check binds the polynomial oracle to the
    # existing tensor without importing any coefficient-generation helper.
    for a in range(8):
        for b in range(64):
            y=0
            for u,v,w in old:
                if ((u&a).bit_count()&1) and ((v&b).bit_count()&1):y^=w
            assert y==oracle(a,b)
    u=[1,1,2,3,3,4,5,5,6,7,7]
    z3.set_param(proof=False);z3.set_param(memory_max_size=768)
    solver=z3.Tactic('sat').solver();solver.set(timeout=round(1000*args.timeout_seconds))
    v=[[z3.Bool(f'vb_{i}_{j}') for j in range(6)] for i in range(11)]
    w=[[z3.Bool(f'wb_{i}_{j}') for j in range(6)] for i in range(11)]
    for i in range(11):solver.add(z3.Or(*v[i]),z3.Or(*w[i]))
    for i in range(10):
        if u[i]==u[i+1]:solver.add(bool_less(v[i],v[i+1]))
    solver.add(exact_word(v[2],1))
    solver.add(z3.Or(*[exact_word(v[j],8) for j in [3,4,8,9,10]]))
    subsets=set()
    for a in range(2,8):
        active=[i for i,f in enumerate(u) if (f&a).bit_count()&1];assert len(active)==6
        for s in range(1,64):subsets.add(tuple(active[k] for k in range(6) if s>>k&1))
    for ss in sorted(subsets):
        for axis in [v,w]:solver.add(z3.Or(*[parity([axis[i][j] for i in ss]) for j in range(6)]))
    for i in range(3):
        for j in range(6):
            expected=oracle(1<<i,1<<j)
            for k in range(6):
                expr=parity([z3.And(v[t][j],w[t][k]) for t in range(11) if u[t]>>i&1])
                solver.add(expr if expected>>k&1 else z3.Not(expr))
    smt=args.out.with_suffix('.smt2');smt.write_text(solver.to_smt2())
    result=dict(status='RUNNING',encoding='Boolean variables with XOR/AND and polynomial oracle; no BitVec',
                source_sha256=sha(__file__),input_sha256=sha(source),z3_version=z3.get_version_string(),
                input_tensor_matches_polynomial_oracle_all_512=True,field_modulus_hex='0xb',tensor_coefficient_equations=108,
                variable_boolean_count=132,first_factors=u,first_v_normalization_index=2,second_v_or_indices=[3,4,8,9,10],
                basis_subset_cuts=2*len(subsets),timeout_seconds=args.timeout_seconds,memory_max_size_mb=768,
                smt2_path=str(smt),smt2_sha256=sha(smt),proof_objects_enabled=False)
    args.out.write_text(json.dumps(result,indent=2)+'\n');print('Independent Boolean/XOR model started',flush=True)
    try:check=solver.check()
    except z3.Z3Exception as error:
        result.update(status='UNKNOWN_NO_RANK_BOUND',reason_unknown=str(error),seconds=time.monotonic()-start)
        args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return
    result.update(solver_result=str(check),seconds=time.monotonic()-start,statistics=str(solver.statistics()),maximum_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    if check==z3.unsat:result.update(status='UNSAT_INDEPENDENT_BOOLEAN_MODEL',proof_path=None)
    elif check==z3.unknown:result.update(status='UNKNOWN_NO_RANK_BOUND',reason_unknown=solver.reason_unknown())
    else:
        model=solver.model();terms=[]
        for i in range(11):
            vi=sum(int(z3.is_true(model.eval(v[i][j],model_completion=True)))<<j for j in range(6))
            wi=sum(int(z3.is_true(model.eval(w[i][j],model_completion=True)))<<j for j in range(6));terms.append([u[i],vi,wi])
        for a in range(8):
            for b in range(64):
                y=0
                for ui,vi,wi in terms:
                    if ((ui&a).bit_count()&1) and ((vi&b).bit_count()&1):y^=wi
                assert y==oracle(a,b)
        result.update(status='SAT_EXACT_ORACLE_VERIFIED',terms=terms,all_512_input_pairs_equal=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
