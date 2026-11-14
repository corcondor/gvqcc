#!/usr/bin/env python3
"""Exact reachable-domain Clifford replacement of CCZ phases.

Unlike the earlier gatewise affine search, this searches all quadratic phase
functions (CZ, Z and NEG) of the currently available wires. Signatures only
solve candidate coefficients; acceptance requires the complete legal domain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import time
import numpy as np

MAX_X=3133452
PIN='e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path)
    ap.add_argument('--report',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();import kickmix as km
    start=time.monotonic();assert hashlib.sha256(args.source.read_bytes()).hexdigest()==PIN
    c=km.Circuit.from_file(str(args.source));lines=str(c).splitlines();n=c.num_qubits
    domain=((1<<(MAX_X+1))-1)^1
    xs=np.arange(MAX_X+1,dtype=np.uint32)
    vals=[int.from_bytes(np.packbits(((xs>>j)&1).astype(np.uint8),bitorder='little').tobytes(),'little')&domain for j in range(22)]+[0]*(n-22)
    initial=vals[:];del xs
    rng=random.Random(20261115051)
    samples=[1,2,3,MAX_X]+[rng.randrange(1,MAX_X+1) for _ in range(2044)]
    sig=[sum(((x>>j)&1)<<i for i,x in enumerate(samples)) for j in range(22)]+[0]*(n-22)
    stack=[];out=[];results=[]

    def quadratic(target,ts):
        masks=[()] + [(i,) for i in range(n)] + [(i,j) for i in range(n) for j in range(i+1,n)]
        signatures=[(1<<len(samples))-1]+sig[:]+[sig[i]&sig[j] for i in range(n) for j in range(i+1,n)]
        width=len(samples)
        for refine in range(len(masks)+1):
            basis={}
            for k,value in enumerate(signatures):
                coeff=1<<k
                while value:
                    p=value.bit_length()-1
                    if p not in basis:basis[p]=(value,coeff);break
                    v,m=basis[p];value^=v;coeff^=m
            value=ts;coeff=0
            while value:
                p=value.bit_length()-1
                if p not in basis:return None,{'decision':'NONMEMBER','refinements':refine,'feature_rank':len(basis)}
                v,m=basis[p];value^=v;coeff^=m
            phase=0;selected=[]
            for k,qs in enumerate(masks):
                if coeff>>k&1:
                    v=domain
                    for q in qs:v&=vals[q]
                    phase^=v;selected.append(qs)
            diff=target^phase
            if not diff:return selected,{'decision':'EXACT_QUADRATIC_MEMBER','refinements':refine,'feature_rank':len(basis),'terms':len(selected)}
            x=(diff&-diff).bit_length()-1
            for k,qs in enumerate(masks):
                bit=1
                for q in qs:bit&=(vals[q]>>x)&1
                signatures[k]|=bit<<width
            ts|=((target>>x)&1)<<width;width+=1
        raise AssertionError('Refinement bound exceeded')

    for i,line in enumerate(lines):
        op=line.split()[0];qs=list(map(int,re.findall(r'\bq(\d+)\b',line)));replacement=None
        if op=='PUSH_CONDITION':stack.append((vals[:],sig[:]))
        elif op=='POP_CONDITION':
            before,bs=stack.pop();assert vals==before,(i,'nonidentity branch');vals,sig=before,bs
        elif op=='X':q,=qs;vals[q]^=domain;sig[q]^=(1<<len(samples))-1
        elif op=='CX':a,t=qs;vals[t]^=vals[a];sig[t]^=sig[a]
        elif op=='CCX':a,b,t=qs;vals[t]^=vals[a]&vals[b];sig[t]^=sig[a]&sig[b]
        elif op=='SWAP':a,b=qs;vals[a],vals[b]=vals[b],vals[a];sig[a],sig[b]=sig[b],sig[a]
        elif op=='CSWAP':
            a,b,d=qs;v=vals[a]&(vals[b]^vals[d]);s=sig[a]&(sig[b]^sig[d]);vals[b]^=v;vals[d]^=v;sig[b]^=s;sig[d]^=s
        elif op=='HMR':q,=qs;vals[q]=sig[q]=0
        elif op=='CCZ':
            target=domain;ts=(1<<len(samples))-1
            for q in qs:target&=vals[q];ts&=sig[q]
            terms,record=quadratic(target,ts);record.update(line=i,before=line,condition_depth=len(stack))
            if terms is not None:
                suffix=(' if '+line.split(' if ',1)[1]) if ' if ' in line else ''
                replacement=[('NEG' if not t else 'Z' if len(t)==1 else 'CZ')+''.join(' q'+str(q) for q in t)+suffix for t in terms]
                record['replacement']=replacement
            results.append(record);print(json.dumps(record),flush=True)
        elif op not in ('Z','CZ','Z_POW','NEG','BIT_INVERT','BIT_STORE0','REGISTER','APPEND_TO_REGISTER'):raise ValueError(line)
        out.extend([line] if replacement is None else replacement)
    assert vals==initial
    hits=sum(r['decision']=='EXACT_QUADRATIC_MEMBER' for r in results)
    report={'status':'COMPLETE','input_sha256':PIN,'valid_inputs':MAX_X,'queries':results,'static_CCZ_removed':hits,'all_final_data_restored':True,'elapsed_seconds':time.monotonic()-start}
    if hits:
        if args.output.exists():raise FileExistsError(args.output)
        candidate=km.Circuit('\n'.join(out)+'\n');candidate.to_file(str(args.output),format='kmb')
        report.update(output=str(args.output),output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest())
    args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='queries'}))


if __name__=='__main__':main()
