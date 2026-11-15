#!/usr/bin/env python3
"""Build sampled cuts; verify every returned relocation identity on all x."""
import json
import argparse
import os
from pathlib import Path
import random
import subprocess
import time
import score_invsqrt_retire as r
from score2_invsqrt_phase_relocation import PANEL

def simulate_targets(ops):
    wanted=[x for x in PANEL if x['old_ANDs']==2];by_phase={x['phase']:x for x in wanted}
    domain,values=r.initial_values();stack=[];targets=[]
    for i,(op,qs) in enumerate(ops):
        if i in by_phase:targets.append((by_phase[i],values[21]))
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
        if i>max(by_phase):break
    return targets

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--global-cuts',action='store_true');args=ap.parse_args()
    base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx');targets=simulate_targets(ops)
    prefix='score2_invsqrt_global_oneand' if args.global_cuts else 'score2_invsqrt_relocate_oneand'
    rng=random.Random(529103);samples=list(range(1,129))
    for k in range(1,22):
        lo=1<<(k-1);hi=min((1<<k)-1,r.MAX_X)
        if lo<=hi:samples += [rng.randrange(lo,hi+1) for _ in range(16)]
    samples=list(dict.fromkeys(samples))
    while len(samples)<512:
        x=rng.randrange(1,r.MAX_X+1)
        if x not in samples:samples.append(x)
    records=[]
    for iteration in range(4):
        width=len(samples);nw=(width+63)//64;sd=(1<<width)-1
        signatures=[sum(((x>>j)&1)<<i for i,x in enumerate(samples)) for j in range(22)]+[0]*24
        target_sig=[sum(((v>>x)&1)<<i for i,x in enumerate(samples)) for item,v in targets]
        domain,values=r.initial_values();stack=[];ss=[];snapshots=[]
        for i,(op,qs) in enumerate(ops):
            if op=='PUSH_CONDITION':stack.append(values[:]);ss.append(signatures[:])
            elif op=='POP_CONDITION':before=stack.pop();sb=ss.pop();assert before==values and sb==signatures;values=before;signatures=sb
            else:r.advance(op,qs,values,domain);r.advance(op,qs,signatures,sd)
            if stack or (not args.global_cuts and not 7572<=i<8390) or op not in ('CCX','CSWAP','HMR'):continue
            zeros=sum(1<<q for q,v in enumerate(values) if not v)
            if not zeros:continue
            snapshots.append((i+1,zeros,signatures[:]))
        def words(v):return [(v>>(64*j))&((1<<64)-1) for j in range(nw)]
        packed=[nw,len(snapshots),len(targets)]+words(sd)
        for (item,v),s in zip(targets,target_sig):packed += [item['start'],item['end']]+words(s)
        for cut,zeros,sig in snapshots:
            packed += [cut,zeros]
            for v in sig:packed+=words(v)
        path=base/f'{prefix}_round{iteration}.txt';path.write_text(' '.join(map(str,packed))+'\n')
        began=time.monotonic();binary=os.environ.get('SCORE2_ONEAND_BINARY','/workspace/scratch/3815fb5fae06/score2_invsqrt_relocate_oneand')
        process=subprocess.run([binary,str(path)],capture_output=True,text=True,timeout=195,check=True)
        result=json.loads(process.stdout);result.update(iteration=iteration,samples=width,elapsed_seconds=time.monotonic()-began)
        (base/f'{prefix}_round{iteration}_progress.jsonl').write_text(process.stderr)
        if result['status']=='SAMPLE_MODEL':
            domain,values=r.initial_values();stack=[]
            for op,qs in ops[:result['cut']]:
                if op=='PUSH_CONDITION':stack.append(values[:])
                elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
                else:r.advance(op,qs,values,domain)
            assert not stack
            item,target=targets[result['target_index']]
            def expr(mask):
                value=0
                for q in range(46):
                    if mask>>q&1:value^=values[q]
                return value
            left=expr(result['left_mask']);right=expr(result['right_mask']);lin=result['affine_mask_constant_then_qubits']
            actual=(left&right)^expr(lin>>1)^(domain if lin&1 else 0);difference=actual^target
            result['feature']=item
            if not difference:
                result['status']='FULL_DOMAIN_IDENTITY_VERIFIED';result['legal_inputs']=r.MAX_X
                records.append(result);print(json.dumps(result),flush=True);break
            x=(difference&-difference).bit_length()-1;result['full_domain_check']='FAIL';result['counterexample']=x;samples.append(x)
        records.append(result);print(json.dumps(result),flush=True)
        if result['status']!='SAMPLE_MODEL':break
    (base/f'{prefix}_results.json').write_text(json.dumps({'scope':'4 two-AND predicates at zero-ancilla cuts; left parity is at most two arbitrary wires or an arbitrary parity of flags q22..q25,q7 plus one arbitrary wire; right parity and affine remainder unrestricted','global_cuts':args.global_cuts,'records':records},indent=2)+'\n')

if __name__=='__main__':main()
