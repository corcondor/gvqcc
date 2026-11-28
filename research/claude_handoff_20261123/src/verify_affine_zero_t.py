#!/usr/bin/env python3
"""Independent all-valid-address exact Boolean and HMR phase verifier for
public-3357 derived ANGLE banks with affine sign-frame angle-table patches.
Sequential composition 15 banks, all 1219 addresses, workspace 128Q;
compare clean and randomized dirty initial word registers.
Phase check is exact per-measurement-bit coefficient on the tested trajectories,
not an official KickMix quantum simulation.
"""
import argparse,hashlib,json,time,random
from pathlib import Path
import numpy as np
from qhdl_kmb import read

def main():
    a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--circuit_dir',required=True);a.add_argument('--out',required=True);a.add_argument('--seeds',type=int,nargs='+',default=[-1,101,202]);p=a.parse_args()
    with np.load(p.source) as z:W=z['angle_words'].astype(np.uint8)
    N=len(W);NN=2048;VALID=(1<<N)-1;FULL=(1<<NN)-1
    allseed=[];time0=time.monotonic()
    for seed in p.seeds:
        t=time.monotonic()
        q=[0]*128
        for j in range(11):q[j]=sum(((n>>j)&1)<<n for n in range(NN))
        sel=q[:11].copy()
        if seed!=-1:
            rng=random.Random(seed)
            for j in range(11,46):q[j]=rng.getrandbits(NN)
        target0=q[11:46].copy()
        banks=[]
        for bank in range(15):
            file=Path(p.circuit_dir)/f'angle_k_{bank}.kmb'
            k=read(str(file));op=k.op_types;S=k.stream
            q1=S('q0');q20=S('qq0');q21=S('qq1');q30=S('qqq0');q31=S('qqq1');q32=S('qqq2');bits=S('b0');conds=S('bc')
            z1=z2=z3=zb=zc=0;phases={};phasefaults=0
            for pos,opcode in enumerate(op):
                v=int(opcode)
                if v==0x11:
                    target=int(q1[z1]);z1+=1;q[target]^=FULL
                elif v==0x21:
                    src,target=int(q20[z2]),int(q21[z2]);z2+=1;q[target]^=q[src]
                elif v==0x31:
                    x,y,target=int(q30[z3]),int(q31[z3]),int(q32[z3]);z3+=1;q[target]^=q[x]&q[y]
                elif v==0x50:
                    wire=int(q1[z1]);b=int(bits[zb]);z1+=1;zb+=1
                    if b in phases:phasefaults+=int(bool(phases[b]&VALID))
                    phases[b]=q[wire];q[wire]=0
                elif v==0x90:
                    wire=int(q1[z1]);b=int(conds[zc]);z1+=1;zc+=1
                    if b not in phases:raise AssertionError(('undeclared bit Z_IF',bank,pos,b))
                    phases[b]^=q[wire]
                elif v==0xa0:
                    x,y=int(q20[z2]),int(q21[z2]);b=int(conds[zc]);z2+=1;zc+=1
                    if b not in phases:raise AssertionError(('undeclared bit CZ_IF',bank,pos,b))
                    phases[b]^=q[x]&q[y]
                else:raise AssertionError(('unsupported gate',bank,pos,hex(v)))
            assert z1==k.counts['q'] and z2==k.counts['qq'] and z3==k.counts['qqq'] and zb==k.counts['b'] and zc==k.counts['c']
            phase_bad=sum(int(bool(s&VALID)) for s in phases.values())+phasefaults
            assert phase_bad==0,('phase',seed,bank,phase_bad)
            assert q[:11]==sel and all(v==0 for v in q[46:]),('scratch',seed,bank)
            errors=0
            for j in range(5):
                for b in range(7):
                    expected=sum((int((W[row,bank*5+j]>>b)&1)<<row) for row in range(N))^target0[7*j+b]
                    errors+=((q[11+7*j+b]^expected)&VALID).bit_count()
            assert errors==0,('value',seed,bank,errors)
            banks.append({'bank':bank,'Toffoli':int(k.counts['qqq']),'Q':int(k.num_qubits),'HMR':int(k.counts['b']),'phase_error_coefficients':int(phase_bad),'value_error_bits':int(errors),'clean_scratch':True,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        allseed.append({'seed':seed,'mode':'clean' if seed==-1 else 'randomized_dirty_initial_words','total_toFFoli_per_pass':sum(x['Toffoli'] for x in banks),'results':banks,'seconds':round(time.monotonic()-t,2)})
        print('PASS',seed,'T',allseed[-1]['total_toFFoli_per_pass'],'15 banks','sec',allseed[-1]['seconds'],flush=True)
    doc={'source_npz':p.source,'source_sha256':hashlib.sha256(Path(p.source).read_bytes()).hexdigest(),'Naddresses':N,'seeds':allseed,'all_tests_pass':True,'native_KickMix':False,'warning':'Basis-state and HMR-phase algebra for clean and randomized dirty initial words; not full formal proof over arbitrary dirty words or official execution','elapsed':time.monotonic()-time0}
    Path(p.out).write_text(json.dumps(doc,indent=2)+'\n')
if __name__=='__main__':main()