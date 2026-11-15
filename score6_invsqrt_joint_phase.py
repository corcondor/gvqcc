#!/usr/bin/env python3
"""Try a joint phase identity, rather than moving each old predicate alone.

For g<=f, alpha*f+beta*g=(alpha+beta)*f-beta*(f XOR g).
If the complement-within-f predicate is affine at another circuit cut, the
old AND/rotation/HMR gadget can be removed without adding rotations or Q.
All proposed identities must pass the complete legal domain.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import json
import random
import time

import score_invsqrt_retire as R
from score2_invsqrt_phase_relocation import PANEL

PIN='d431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decimal(angle):
    angle %= 2
    n,d=angle.numerator,angle.denominator
    assert d&(d-1)==0
    k=d.bit_length()-1
    if not k:return str(n)
    digits=str(n*5**k).rjust(k+1,'0')
    return (digits[:-k]+'.'+digits[-k:]).rstrip('0').rstrip('.')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();root=Path(__file__).parent
    source=root/'score3_invsqrt_cache.kmx';assert sha(source)==PIN
    lines,ops=R.instructions(source)
    # score3 inserted four lines before this phase region; the old scoped
    # gadgets are unchanged and still have complete restoring boundaries.
    panel=[{**p,'start':p['start']+4,'phase':p['phase']+4,'end':p['end']+4} for p in PANEL]
    domain,values=R.initial_values();stack=[];rotations=[];original_targets={}
    for i,(op,qs) in enumerate(ops):
        if op=='Z_POW':
            assert not stack and ' if ' not in lines[i]
            rotations.append(dict(index=i,line=i+1,q=qs[0],truth=values[qs[0]],angle=Fraction(lines[i].split()[2])))
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':saved=stack.pop();assert saved==values;values=saved
        else:R.advance(op,qs,values,domain)
    by_phase={row['index']:row for row in rotations};targets=[]
    for gadget in panel:
        g=by_phase[gadget['phase']]
        assert g['q']==21
        # The paired base-bit rotation is immediately before the gadget.
        f=by_phase[gadget['start']-1]
        assert not(g['truth']&~f['truth'])
        targets.append(dict(gadget=gadget,base=f,feature=g,truth=f['truth']^g['truth']))
    rng=random.Random(620261115)
    samples=list(range(1,4097))+[rng.randrange(1,R.MAX_X+1) for _ in range(512)]
    signatures=[sum(((x>>q)&1)<<i for i,x in enumerate(samples)) for q in range(22)]+[0]*24
    target_sigs=[sum(((row['truth']>>x)&1)<<i for i,x in enumerate(samples)) for row in targets]
    sample_domain=(1<<len(samples))-1
    domain,values=R.initial_values();stack=[];sample_stack=[];queries=0;cuts=0;found=[];refinements=[]
    found_ids=set()
    for i,(op,qs) in enumerate(ops):
        if op=='PUSH_CONDITION':stack.append(values[:]);sample_stack.append(signatures[:])
        elif op=='POP_CONDITION':
            saved=stack.pop();ss=sample_stack.pop();assert saved==values and ss==signatures;values=saved;signatures=ss
        else:R.advance(op,qs,values,domain);R.advance(op,qs,signatures,sample_domain)
        if stack or op not in ('CCX','CSWAP','HMR'):continue
        cut=i+1
        # Exclude every removable gadget, so independently found plans may
        # compose without their insertion site being deleted by another plan.
        if any(g['start']<=cut<=g['end'] for g in panel):continue
        cuts+=1
        while True:
            basis=R.affine_basis([sample_domain]+signatures);retry=False
            for j,row in enumerate(targets):
                if j in found_ids:continue
                queries+=1;coefficient=R.solve(basis,target_sigs[j])
                if coefficient is None:continue
                actual=domain if coefficient&1 else 0
                wires=[q for q in range(46) if coefficient>>(q+1)&1]
                for q in wires:actual^=values[q]
                difference=actual^row['truth']
                if difference:
                    x=(difference&-difference).bit_length()-1;bit=1<<len(samples)
                    for q in range(46):signatures[q]|=((values[q]>>x)&1)*bit
                    for k,item in enumerate(targets):target_sigs[k]|=((item['truth']>>x)&1)*bit
                    sample_domain|=bit;samples.append(x);refinements.append(dict(cut=cut,target=j,x=x));retry=True;break
                plan=dict(target=j,name=row['gadget']['name'],insert_after_line=cut,
                          constant=coefficient&1,parity_qubits=wires,
                          remove_start=row['gadget']['start'],remove_end=row['gadget']['end'],
                          base_rotation_line=row['base']['line'],old_ANDs=row['gadget']['old_ANDs'],
                          old_base_angle=str(row['base']['angle']),old_feature_angle=str(row['feature']['angle']),
                          exact_identity='g<=f; alpha*f+beta*g=(alpha+beta)*f-beta*(f XOR g)',
                          full_domain_predicate_check=True)
                found.append(plan);found_ids.add(j);print(json.dumps({'found':plan}),flush=True)
            if not retry:break
    report=dict(status='COMPLETE_EXACT_JOINT_PHASE_SCREEN',source_path=str(source),source_sha256=PIN,
                legal_inputs=R.MAX_X,targets=len(targets),eligible_cuts=cuts,queries=queries,
                final_sample_rows=len(samples),refinements=refinements,plans=found,
                scope='Eight nested phase pairs. Search affine complement-within-base predicates at all depth-zero CCX/CSWAP/HMR cuts outside every removed gadget. General phase resynthesis is not exhausted.',
                exact_pair_supports=[dict(name=row['gadget']['name'],base=row['base']['truth'].bit_count(),
                                         subset=row['feature']['truth'].bit_count(),
                                         complement=row['truth'].bit_count()) for row in targets])
    if found:
        # Independent plans restore their borrowed parity pivot immediately;
        # all removed gadgets return their touched data/scratch to entry.
        by_insert={};delete=set();angle_changes={}
        for plan in found:
            row=targets[plan['target']];wires=plan['parity_qubits'];assert wires
            pivot=wires[0];add=[f'CX q{q} q{pivot}' for q in wires[1:]]
            if plan['constant']:add.append(f'X q{pivot}')
            add.append(f"Z_POW q{pivot} {decimal(-row['feature']['angle'])}")
            if plan['constant']:add.append(f'X q{pivot}')
            add.extend(f'CX q{q} q{pivot}' for q in reversed(wires[1:]))
            by_insert.setdefault(plan['insert_after_line'],[]).extend(add)
            delete.update(range(plan['remove_start'],plan['remove_end']))
            angle_changes[row['base']['index']]=f"Z_POW q{row['base']['q']} {decimal(row['base']['angle']+row['feature']['angle'])}"
        output=[]
        for i,line in enumerate(lines):
            if i not in delete:output.append(angle_changes.get(i,line))
            output.extend(by_insert.get(i+1,[]))
        kmx=args.out/'candidate.kmx';kmx.write_text('\n'.join(output)+'\n')
        import kickmix as km
        c=km.Circuit(kmx.read_text());base=km.Circuit(source.read_text());kmb=args.out/'candidate.kmb';c.to_file(kmb,format='kmb')
        report.update(status='EXACT_JOINT_PHASE_CANDIDATE_BUILT_LOCAL_NATIVE_PENDING',
                      output_path=str(kmb),output_sha256=sha(kmb),static_T=c.operation_statistics().num_toffoli_like,
                      static_T_delta=c.operation_statistics().num_toffoli_like-base.operation_statistics().num_toffoli_like,
                      Q=c.num_qubits,full_official_verified=False)
    report['elapsed_seconds']=time.monotonic()-start;report['script_sha256']=sha(__file__)
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('refinements','plans','exact_pair_supports')},indent=2))


if __name__=='__main__':main()
