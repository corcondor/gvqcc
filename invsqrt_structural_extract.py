#!/usr/bin/env python3
"""Extract deterministic Boolean phase bases on all legal x, no measurement sampling.
This takes the all-zero HMR outcome branch; native random-outcome validation is
separate and required before accepting a changed phase architecture.
"""
import argparse,json,pathlib,subprocess
from fractions import Fraction

def main():
 p=argparse.ArgumentParser();p.add_argument('--kmx',default='gvqcc_repo/invsqrt_structural_e46.kmx');p.add_argument('--out',default='invsqrt_structural_work');a=p.parse_args()
 out=pathlib.Path(a.out);out.mkdir(exist_ok=True)
 text=pathlib.Path(a.kmx).read_text().splitlines();ops=[];basis=[];snapshots=[];active=[True];bits={}
 types={'X':0,'CX':1,'CCX':2,'SWAP':3,'CSWAP':4,'HMR':5,'Z':6,'CZ':7,'CCZ':8,'NEG':9}
 for lineno,line in enumerate(text,1):
  w=line.split();name=w[0]
  if lineno in (7705,8075,8189):
   for q in range(46):
    j=len(basis);basis.append({'kind':'snapshot','line':lineno,'qubit':q});snapshots.append(j);ops.append((10,q,j,0))
  if name=='PUSH_CONDITION': active.append(active[-1] and bits.get(int(w[-1][1:]),False));continue
  if name=='POP_CONDITION': active.pop();continue
  enabled=active[-1]
  if 'if' in w: enabled=enabled and bits.get(int(w[w.index('if')+1][1:]),False);w=w[:w.index('if')]
  if not enabled:continue
  if name in ('APPEND_TO_REGISTER','REGISTER'):continue
  if name=='HMR':bits[int(w[2][1:])]=False
  if name=='BIT_STORE0':bits[int(w[1][1:])]=False;continue
  if name=='BIT_INVERT':k=int(w[1][1:]);bits[k]=not bits.get(k,False);continue
  if name=='Z_POW':
   angle=Fraction(w[2]);j=len(basis);basis.append({'kind':'rotation','line':lineno,'qubit':int(w[1][1:]),'half_turns':str(angle),'turns':float(angle/2),'class':'clifford' if angle%Fraction(1,2)==0 else 't' if angle%Fraction(1,4)==0 else 'rotation'});ops.append((10,int(w[1][1:]),j,0));continue
  if name not in types:raise ValueError((lineno,w))
  qs=[int(s[1:]) for s in w[1:] if s.startswith('q')];ops.append(tuple([types[name]]+qs+[0]*(3-len(qs))))
 basis.append({'kind':'phase_parity','line':len(text),'turns':.5})
 (out/'basis.json').write_text(json.dumps({'max_x':3133452,'basis':basis,'ops':len(ops)},indent=2))
 (out/'ops.txt').write_text('\n'.join(' '.join(map(str,x)) for x in ops))
 print(json.dumps({'basis':len(basis),'ops':len(ops),'snapshots':len(snapshots)}),flush=True)
 src=r'''#include <cstdio>
#include <cstdint>
#include <vector>
#include <fstream>
#include <iostream>
#include <string>
using U=uint64_t; struct O{int t,a,b,c;};
int main(int argc,char**argv){int nb=std::stoi(argv[2]); const int n=3133452; int nw=(n+63)/64;std::string d=argv[1];std::vector<O>ops; O o;std::ifstream in(d+"/ops.txt");while(in>>o.t>>o.a>>o.b>>o.c)ops.push_back(o); std::vector<U> b((size_t)nb*nw);U q[46];unsigned long long bad=0;
for(int w=0;w<nw;w++){for(int j=0;j<46;j++)q[j]=0;for(int l=0;l<64;l++){int x=w*64+l+1;for(int j=0;j<22;j++)q[j]|=U((x>>j)&1)<<l;}U phase=0;
for(auto o:ops){switch(o.t){case 0:q[o.a]=~q[o.a];break;case 1:q[o.b]^=q[o.a];break;case 2:q[o.c]^=q[o.a]&q[o.b];break;case 3:{U t=q[o.a];q[o.a]=q[o.b];q[o.b]=t;break;}case 4:{U t=q[o.a]&(q[o.b]^q[o.c]);q[o.b]^=t;q[o.c]^=t;break;}case 5:q[o.a]=0;break;case 6:phase^=q[o.a];break;case 7:phase^=q[o.a]&q[o.b];break;case 8:phase^=q[o.a]&q[o.b]&q[o.c];break;case 9:phase=~phase;break;case 10:b[(size_t)o.b*nw+w]=q[o.a];break;}}
b[(size_t)(nb-1)*nw+w]=phase;for(int l=0;l<64&&w*64+l<n;l++){int x=w*64+l+1;bool ok=true;for(int j=0;j<22;j++)if(((q[j]>>l)&1)!=((x>>j)&1))ok=false;for(int j=22;j<46;j++)if((q[j]>>l)&1)ok=false;if(!ok)bad++;}}
std::ofstream f(d+"/basis.u64",std::ios::binary);f.write((char*)b.data(),b.size()*8);std::cout<<"{\"bad_restoration\":"<<bad<<",\"words_per_basis\":"<<nw<<"}"<<std::endl;return bad?1:0;}
'''
 cpp=out/'extract.cpp';cpp.write_text(src);subprocess.run(['g++','-O3','-std=c++17',str(cpp),'-o',str(out/'extract')],check=True);subprocess.run([str(out/'extract'),str(out),str(len(basis))],check=True)
if __name__=='__main__':main()
