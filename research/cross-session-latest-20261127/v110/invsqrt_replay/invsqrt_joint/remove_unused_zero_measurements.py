#!/usr/bin/env python3
"""Remove unobserved measurements of syntactically known-zero qubits.

Each deletion has two independent conditions: a conservative constant tracker
proves the measured quantum wire is |0>, and backwards liveness proves the
classical outcome unobserved. The checker compares expanded classical ANF
guards at every remaining quantum event, with original HMR variable labels.
Final unregistered classical scratch values are not an observable.
"""
import argparse, collections, hashlib, json, re, sys
from pathlib import Path
import kickmix as km
sys.path.insert(0,str(Path(__file__).parent))
from classical_cleanup import load,ClassicalANF,ONE,ZERO,mul


def known_zero_hmrs(lines,nq,parse):
    zero=[False]*22+[True]*(nq-22);depth=0;found=set()
    for i,l in enumerate(lines):
        n,qs,cb,d=parse(l)
        unconditional=depth==0 and cb is None
        if n=='PUSH_CONDITION':depth+=1
        elif n=='POP_CONDITION':depth-=1
        elif n=='X':zero[qs[0]]=False
        elif n=='CX':
            if not zero[qs[0]]:zero[qs[1]]=False
        elif n=='CCX':
            if not (zero[qs[0]] or zero[qs[1]]):zero[qs[2]]=False
        elif n=='SWAP':
            u,v=qs
            if unconditional:zero[u],zero[v]=zero[v],zero[u]
            elif not (zero[u]and zero[v]):zero[u]=zero[v]=False
        elif n=='CSWAP':
            ctrl,u,v=qs
            if not zero[ctrl] and not (zero[u]and zero[v]):zero[u]=zero[v]=False
        elif n=='HMR':
            if zero[qs[0]]:found.add(i)
            if unconditional:zero[qs[0]]=True
    assert depth==0
    return found


def optimize(pairs,nq,nb,parse):
    ls=[l for _,l in pairs];zero=known_zero_hmrs(ls,nq,parse);depth=0;depths=[]
    for l in ls:
        if l=='POP_CONDITION':depth-=1
        depths.append(depth)
        if l.startswith('PUSH_CONDITION'):depth+=1
    live=set();keep=[];removed=[]
    for i in range(len(pairs)-1,-1,-1):
        original,l=pairs[i];n,qs,cb,d=parse(l);unconditional=depths[i]==0 and cb is None
        if n=='HMR' and i in zero and d not in live:
            removed.append(dict(original_line=original,instruction=l,reason='known-zero HMR with unobserved outcome'));continue
        if n.startswith('BIT_'):
            if d not in live:
                removed.append(dict(original_line=original,instruction=l,reason='unobserved classical scratch write'));continue
            if n in ('BIT_STORE0','BIT_STORE1') and unconditional:live.discard(d)
            else:live.add(d)
        elif n=='HMR':
            if unconditional:live.discard(d)
            else:live.add(d)
        if cb is not None:live.add(cb)
        keep.append(pairs[i])
    keep.reverse();stack=[]
    for pair in keep:
        if pair[1]=='POP_CONDITION' and stack and stack[-1][1].startswith('PUSH_CONDITION'):
            before=stack.pop();removed.extend(dict(original_line=k,instruction=l,reason='empty condition scope') for k,l in [before,pair])
        else:stack.append(pair)
    return stack,removed


def verify(old,newpairs,nq,nb,parse,removed):
    omitted={r['original_line'] for r in removed if r['reason']=='known-zero HMR with unobserved outcome'};zero=known_zero_hmrs(old,nq,parse);assert omitted<=zero
    # A second, simpler zero proof: each omitted HMR follows an unconditional
    # reset with no intervening possible value write to that wire. This checker
    # does not reuse the optimizer's control-zero propagation rules.
    reset=[None]*22+[-1]*(nq-22);depth=0;reset_certificates=[]
    for i,l in enumerate(old):
        n,qs,cb,d=parse(l)
        if i in omitted:
            assert reset[qs[0]] is not None,(i,l)
            reset_certificates.append(dict(line=i,wire=qs[0],preceding_unconditional_HMR_line=reset[qs[0]],no_intervening_possible_value_write=True))
        if n=='PUSH_CONDITION':depth+=1
        elif n=='POP_CONDITION':depth-=1
        elif n in ('X','CX','CCX'):reset[qs[-1]]=None
        elif n in ('SWAP','CSWAP'):
            for q in qs[-2:]:reset[q]=None
        elif n=='HMR' and cb is None and depth==0:reset[qs[0]]=i
    original_hmr={};j=0
    for i,l in enumerate(old):
        if l.startswith('HMR'):original_hmr[i]=j;j+=1
    a=ClassicalANF(nb,parse);b=ClassicalANF(nb,parse)
    def events(pairs,S,omit):
        for i,l in pairs:
            if l.startswith('HMR'):S.hmr=original_hmr[i]
            e=S.step(l)
            if e is not None and i not in omit:yield i,e
    ea=events(list(enumerate(old)),a,omitted);eb=events(newpairs,b,set());count=0
    for x in ea:
        y=next(eb,None);assert x==y,(x,y);count+=1
    assert next(eb,None) is None and a.scope==b.scope==[ONE]
    return dict(status='PASS',quantum_events_retained=count,removed_known_zero_HMR=len(omitted),every_remaining_quantum_guard_equal=True,
                all_original_HMR_outcomes_formal=True,measurement_labels='Original serialized HMR index; deleted outcome variables are traced out, not fixed or postselected.',
                final_classical_values_not_observed=True,independent_reset_certificates=reset_certificates,method='Independent reset/no-write certificates plus independent expanded Boolean ANF of every retained effective quantum guard')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--trace-source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();m=load(a.trace_source);c=km.Circuit.from_file(a.input);old=str(c).splitlines();pairs=list(enumerate(old));removed=[]
    while True:
        new,rr=optimize(pairs,c.num_qubits,c.num_bits,m.parse);removed.extend(rr)
        if new==pairs:break
        pairs=new
    proof=verify(old,pairs,c.num_qubits,c.num_bits,m.parse,removed);d=km.Circuit('\n'.join(l for _,l in pairs)+'\n');a.out.mkdir(parents=True,exist_ok=True);f=a.out/'invsqrt.kmb';d.to_file(f,format='kmb');assert str(km.Circuit.from_file(f))==str(d)
    r=dict(status='EXACT_QUANTUM_CHANNEL_UNUSED_ZERO_MEASUREMENT_REMOVAL',input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),before=len(c),after=len(d),qubits=d.num_qubits,paid_before=c.operation_statistics().num_toffoli_like,paid_after=d.operation_statistics().num_toffoli_like,removed_count=len(removed),removed_by_reason=dict(collections.Counter(x['reason']for x in removed)),removed=removed,independent_proof=proof)
    (a.out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='removed'},indent=2))


if __name__=='__main__':main()