"""Matched native replay of the published #268 DQI witness, with full support basis.
The native score from an ordinary panel is not inferred from this fixed input.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import kickmix as km
import verify_submission_dqi as V

CIRCUIT_SEED_HASH='8db1fd9d2b03979e355659e8cf2df421c3938e44133a5b760c9e7242d5afe9b9'
SPEC=V.ProblemSpecDQI.benchmark_instance(num_shots=102400)


def official(w):
    ss=np.random.SeedSequence(int(CIRCUIT_SEED_HASH,16),pool_size=8)
    row=ss.generate_state(8*400,dtype=np.uint64).reshape(-1,2,4)[w['batch']]
    t,s=[int.from_bytes(x,'little') for x in row]
    assert s==int(w['seed'])
    table=V.FieldTables(km.GF2Field(12))
    p=V.optimal_dqi_weights(SPEC.m,SPEC.max_errors,SPEC.degree,SPEC.r)**2
    data,mask,phase=V.sample_shots(SPEC,table,np.random.default_rng(t),256,p)
    assert data[w['lane']].tolist()==w['syndrome']
    assert bool(phase[w['lane']])==w['expected_phase']
    return mask[w['lane']],s


def run(path, fixture, original, original_seed):
    tape=km.Circuit.from_file(str(path))
    q,m,a=map(km.array,V.validate_registers(tape,SPEC))
    S=np.asarray(fixture['syndrome'],dtype=np.uint16)
    support=fixture['support']
    e=np.asarray(fixture['magnitudes'],dtype=np.uint16)
    parity=np.array([k.bit_count()%2 for k in range(4096)],dtype=np.uint8)
    assert len(set(support))==fixture['weight']==32

    def run_block(masks, seed):
        n=len(masks)
        ss=np.repeat(S[None,:],n,axis=0)
        X,Y=V.to_bits(ss,12),V.to_bits(masks,12)
        expected=parity[masks[:,support]&e].sum(1)%2
        sim=km.Simulator(batch_size=n,seed=int(seed),counting_operations=True,debug_print=False)
        sim.use_same_registers_as(tape)
        sim.write_across_shots(q,X)
        sim.write_across_shots(m,Y)
        sim.do(tape)
        return np.array([(sim.read_across_shots(q)!=X).any(0),
            sim.read_phase_flipped_across_shots()^expected.astype(bool),
            sim.read_across_shots(a).any(0),(sim.read_across_shots(m)!=Y).any(0)]),sim.operation_statistics().num_toffoli_like

    r=np.random.default_rng(268384)
    base=np.zeros((64,4095),dtype=np.uint16)
    base[1:]=original
    on=[(j,k) for j in support for k in range(12)]
    offs=r.choice(np.array([i for i in range(4095*12) if i//12 not in set(support)]),size=256,replace=False)
    off=[divmod(int(i),12) for i in offs]
    req=on+off
    all_results=[]
    for seed in (original_seed,0x268):
        e0,p0=run_block(base,seed)
        bias=bool(e0[1,0])
        mismatched=[]
        totals=np.zeros(4,dtype=np.int64)
        for i in range(0,len(req),128):
            b=req[i:i+128]
            M=np.zeros((len(b),4095),np.uint16)
            for k,(j,l) in enumerate(b):M[k,j]=1<<l
            x,_=run_block(M,seed)
            totals+=x.sum(1)
            mismatched.extend([list(b[k]) for k in np.flatnonzero(x[1]^bias)])
        x=r.integers(0,4096,(64,4095),dtype=np.uint16)
        y=r.integers(0,4096,(64,4095),dtype=np.uint16)
        z,p=run_block(np.concatenate((x,y,x^y)),seed)
        nonlinearity=int((z[1,:64]^z[1,64:128]^z[1,128:]^bias).sum())
        all_results.append(dict(seed=str(seed),zero_mask_errors=e0[:,0].astype(int).tolist(),
            captured_mask_errors=e0[:,1:].sum(1).tolist(),onehot_error_totals=totals.tolist(),
            phase_diff_support=[p for p in mismatched if p[0] in support],
            phase_diff_sample_off_support=[p for p in mismatched if p[0] not in support],
            randomized_pair_linearity_violations=nonlinearity,randomized_mask_errors=z.sum(1).tolist(),
            fixed_syndrome_paid_per_shot=p0/64))
        print(path,seed,totals.tolist(),len(mismatched),nonlinearity,flush=True)
    return dict(file=path.name,sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),
        qubits=tape.num_qubits,operations=len(tape),static_paid=tape.operation_statistics().num_toffoli_like,
        basis_support=384,off_support_sample=256,results=all_results)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('fixture',type=Path)
    ap.add_argument('out',type=Path)
    ap.add_argument('tapes',type=Path,nargs='+')
    a=ap.parse_args()
    w=json.loads(a.fixture.read_text())
    m,s=official(w)
    rows=[]
    for p in a.tapes:
        rows.append(run(p,w,m,s))
        a.out.write_text(json.dumps(dict(error_order=['value','phase','dirty','mask'],
            batch=w['batch'],lane=w['lane'],seed_hash=CIRCUIT_SEED_HASH,circuits=rows),indent=2)+'\n')


if __name__=='__main__':
    main()
