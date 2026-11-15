#!/usr/bin/env python3
"""Bounded two-CCX dirty-target replacement using the existing one-AND solver."""
from pathlib import Path
import hashlib,json,re,random,subprocess,time,argparse
import score_invsqrt_retire as r


def expr(mask,values,domain):
    value=domain if mask&1 else 0
    for q in range(46):
        if mask>>(q+1)&1:value^=values[q]
    return value


def replacement(left,right,linear,target):
    left&=~(1<<target);right&=~(1<<target);linear&=~(1<<(target+1))
    lines=[];count=0
    if left and right:
        if left==right:linear^=left<<1
        else:
            a=(left&-left).bit_length()-1
            prepare=[f'CX q{q} q{a}' for q in range(46) if q!=a and left>>q&1]
            transformed=right^(left^(1<<a)) if right>>a&1 else right
            possible=transformed&~(1<<a)
            if not possible:raise AssertionError('Dependent prepared controls')
            b=(possible&-possible).bit_length()-1
            prepare += [f'CX q{q} q{b}' for q in range(46) if q!=b and transformed>>q&1]
            lines+=prepare+[f'CCX q{a} q{b} q{target}']+list(reversed(prepare));count=1
    if linear&1:lines.append(f'X q{target}')
    lines += [f'CX q{q} q{target}' for q in range(46) if linear>>(q+1)&1]
    return lines,count


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True);began=time.monotonic();base=Path(__file__).parent
    path=base/'invsqrt_structural_e46.kmx';lines,ops=r.instructions(path)
    profile=json.loads((base/'score3_invsqrt_pair_profile.json').read_text())
    panel=[pair for pair in profile['pairs'] if pair['first']>10000]
    starts={pair['first'] for pair in panel};states={};domain,values=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i in starts:assert not stack;states[i]=values[:]
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':old=stack.pop();assert old==values;values=old
        else:r.advance(op,qs,values,domain)
    binary=Path('/workspace/scratch/3815fb5fae06/score2_invsqrt_relocate_oneand')
    if not binary.exists():
        binary=a.out/'solver';subprocess.run(['g++','-O3','-std=c++17',str(base/'score2_invsqrt_relocate_oneand.cpp'),'-o',str(binary)],check=True)
    rng=random.Random(2026111503);samples=list(range(1,129))
    for k in range(1,23):
        lo=1<<(k-1);hi=min((1<<k)-1,r.MAX_X)
        if lo<=hi:samples += [rng.randrange(lo,hi+1) for _ in range(12)]
    samples=list(dict.fromkeys(samples))
    while len(samples)<512:
        x=rng.randrange(1,r.MAX_X+1)
        if x not in samples:samples.append(x)
    records=[];patches=[]
    for index,pair in enumerate(panel):
        first,second,target=pair['first'],pair['second'],pair['start_target'];entry=states[first]
        frame=[1<<(q+1) for q in range(46)]
        for op,qs in ops[first+1:second]:
            if op=='X':frame[qs[0]]^=1
            elif op=='CX':frame[qs[1]]^=frame[qs[0]]
            elif op=='SWAP':frame[qs[0]],frame[qs[1]]=frame[qs[1]],frame[qs[0]]
            else:raise AssertionError(op)
        a1,b1,_=ops[first][1];a2,b2,_=ops[second][1]
        truth=(entry[a1]&entry[b1])^(expr(frame[a2],entry,domain)&expr(frame[b2],entry,domain))
        assert not((frame[a2]|frame[b2])>>(target+1)&1)
        sample_list=list(samples);attempts=[];accepted=None
        for iteration in range(5):
            width=len(sample_list);nw=(width+63)//64;one=(1<<width)-1
            def signature(v):return sum(((v>>x)&1)<<i for i,x in enumerate(sample_list))
            def words(v):return [(v>>(64*j))&((1<<64)-1) for j in range(nw)]
            packed=[nw,1,1]+words(one)+[-1,-1]+words(signature(truth))+[first,0]
            for q in range(46):packed+=words(0 if q==target else signature(entry[q]))
            query=a.out/f'pair{index}_round{iteration}.txt';query.write_text(' '.join(map(str,packed))+'\n')
            process=subprocess.run([str(binary),str(query)],capture_output=True,text=True,check=True,timeout=110)
            result=json.loads(process.stdout);result['samples']=width;attempts.append(result)
            if result['status']!='SAMPLE_MODEL':break
            left=result['left_mask']&~(1<<target);right=result['right_mask']&~(1<<target)
            linear=result['affine_mask_constant_then_qubits']&~(1<<(target+1))
            actual=(expr(left<<1,entry,domain)&expr(right<<1,entry,domain))^expr(linear,entry,domain)
            difference=actual^truth
            if difference:
                witness=(difference&-difference).bit_length()-1;sample_list.append(witness);result['counterexample']=witness;continue
            new,count=replacement(left,right,linear,target)
            new+=lines[first+1:second]
            expected=entry[:];computed=entry[:]
            for op,qs in ops[first:second+1]:r.advance(op,qs,expected,domain)
            for line in new:r.advance(line.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',line))),computed,domain)
            assert expected==computed
            accepted=dict(status='FULL_DOMAIN_WINDOW_IDENTITY',legal_inputs=r.MAX_X,
                          left_mask=left,right_mask=right,affine_mask=linear,new_ccx=count,removed_ccx=2-count,
                          phase_free=True,all46_output_values_equal=True,replacement=new)
            patches.append(dict(pair,**accepted));break
        record=dict(pair,attempts=attempts,result=accepted or dict(status='NO_MODEL_IN_TESTED_LEFT_FAMILY'))
        records.append(record);print(json.dumps({k:v for k,v in record.items() if k!='attempts'}),flush=True)
    report=dict(status='BOUNDED_DIRTY_PAIR_SCAN_COMPLETE',eligible_windows=profile['eligible'],new_windows_tested=len(panel),
                prior_phase_windows_skipped=2,records=records,accepted=len(patches),
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                solver_source_sha256=hashlib.sha256((base/'score2_invsqrt_relocate_oneand.cpp').read_bytes()).hexdigest(),
                scope='Same transported dirty-target direction; only unconditional X/CX/SWAP between two adjacent CCX; all-live factors excluding the target. Left family includes singles/pairs and existing solver flag-parity extensions; right and affine remainder unrestricted.',
                seconds=time.monotonic()-began,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if patches:
        output=[];position=0
        for patch in patches:
            output+=lines[position:patch['first']]+patch['replacement'];position=patch['second']+1
        output+=lines[position:]
        kmx=a.out/'candidate.kmx';kmx.write_text('\n'.join(output)+'\n')
        import kickmix as km
        old=km.Circuit(path.read_text());candidate=km.Circuit(kmx.read_text());kmb=a.out/'candidate.kmb';candidate.to_file(kmb,format='kmb')
        report.update(candidate_kmx=str(kmx),candidate_kmb=str(kmb),candidate_qubits=candidate.num_qubits,
                      removed_ccx=int(old.operation_statistics().num_toffoli_like-candidate.operation_statistics().num_toffoli_like),
                      candidate_sha256=hashlib.sha256(kmb.read_bytes()).hexdigest(),full_official_run=False)
        assert candidate.num_qubits==46
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2),flush=True)


if __name__=='__main__':main()
