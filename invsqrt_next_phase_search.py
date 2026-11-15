#!/usr/bin/env python3
"""Search phase rotations on deterministic forward arithmetic values.

The gate sequence and all measurement corrections are kept.  A snapshot after
an unconditional Boolean gate before the final phase rotation is a function of
x, independent of all prior measurement outcomes.  The parser checks that all
conditional operations before that point are diagonal or classical.
"""
import argparse, json, pathlib, subprocess, time, hashlib
from fractions import Fraction
import numpy as np
from scipy.optimize import linprog

N=3133452
SCALE=1e-11
SOURCE=pathlib.Path('/workspace/scratch/7f542e06b7cf/gvqcc_repo/score3_invsqrt_cache.kmx')
WORK=pathlib.Path('/workspace/scratch/4020ae2c83bc/invsqrt_next_work')
OUT=pathlib.Path(__file__).parent

CPP=r'''#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
using U=uint64_t; struct O{int t,a,b,c;};
int main(int argc,char**argv){std::string dir=argv[1],tag=argv[2];int nf=std::stoi(argv[3]);
std::vector<int>xs;int v;std::ifstream ix(dir+"/"+tag+".inputs");while(ix>>v)xs.push_back(v);
int n=xs.size(),nw=(n+63)/64;std::vector<O>ops;O o;std::ifstream io(dir+"/"+tag+".ops");while(io>>o.t>>o.a>>o.b>>o.c)ops.push_back(o);
std::vector<U> out((size_t)nf*nw);U q[46];size_t bad=0;
for(int w=0;w<nw;w++){for(int j=0;j<46;j++)q[j]=0;for(int l=0;l<64&&w*64+l<n;l++){int x=xs[w*64+l];for(int j=0;j<22;j++)q[j]|=U((x>>j)&1)<<l;}U phase=0;
for(auto o:ops)switch(o.t){case 0:q[o.a]=~q[o.a];break;case 1:q[o.b]^=q[o.a];break;case 2:q[o.c]^=q[o.a]&q[o.b];break;case 3:{U a=q[o.a];q[o.a]=q[o.b];q[o.b]=a;break;}case 4:{U t=q[o.a]&(q[o.b]^q[o.c]);q[o.b]^=t;q[o.c]^=t;break;}case 5:q[o.a]=0;break;case 6:phase^=q[o.a];break;case 7:phase^=q[o.a]&q[o.b];break;case 8:phase^=q[o.a]&q[o.b]&q[o.c];break;case 9:phase=~phase;break;case 10:out[(size_t)o.b*nw+w]=q[o.a];break;}
out[(size_t)(nf-1)*nw+w]=phase;
for(int l=0;l<64&&w*64+l<n;l++){int x=xs[w*64+l];bool ok=true;for(int j=0;j<46;j++)if(((q[j]>>l)&1)!=(j<22?((x>>j)&1):0))ok=false;bad+=!ok;}}
std::ofstream f(dir+"/"+tag+".u64",std::ios::binary);f.write((char*)out.data(),out.size()*8);std::cout<<"restoration_bad="<<bad<<" n="<<n<<" features="<<nf<<std::endl;return bad?1:0;}
'''

def parse(source, selected=None, all_candidates=False):
    text=source.read_text().splitlines();ops=[];desc=[];bits={};active=[True]
    lastrot=max(i+1 for i,s in enumerate(text) if s.startswith('Z_POW '))
    types={'X':0,'CX':1,'CCX':2,'SWAP':3,'CSWAP':4,'HMR':5,'Z':6,'CZ':7,'CCZ':8,'NEG':9}
    conditional_bad=[]
    selected=set(selected or [])
    for line,s in enumerate(text,1):
        w=s.split();name=w[0]
        if name=='PUSH_CONDITION':active.append(active[-1] and bits.get(int(w[-1][1:]),False));continue
        if name=='POP_CONDITION':active.pop();continue
        conditioned=len(active)>1 or 'if' in w
        if line<=lastrot and conditioned and name not in ('Z','CZ','CCZ','NEG','BIT_STORE0','BIT_STORE1','BIT_INVERT'):
            conditional_bad.append([line,s])
        enabled=active[-1]
        if 'if' in w:enabled=enabled and bits.get(int(w[w.index('if')+1][1:]),False);w=w[:w.index('if')]
        if not enabled:continue
        if name in ('APPEND_TO_REGISTER','REGISTER'):continue
        if name=='HMR':bits[int(w[2][1:])]=False
        if name in ('BIT_STORE0','BIT_STORE1'):bits[int(w[1][1:])]=name=='BIT_STORE1';continue
        if name=='BIT_INVERT':k=int(w[1][1:]);bits[k]=not bits.get(k,False);continue
        if name=='Z_POW':
            a=Fraction(w[2]);q=int(w[1][1:]);j=len(desc)
            desc.append({'kind':'rotation','line':line,'qubit':q,'half_turns':str(a),'class':'clifford' if a%Fraction(1,2)==0 else 't' if a%Fraction(1,4)==0 else 'rotation'})
            ops.append((10,q,j,0));continue
        if name not in types:raise ValueError((line,w))
        qs=[int(x[1:]) for x in w[1:] if x.startswith('q')]
        ops.append(tuple([types[name]]+qs+[0]*(3-len(qs))))
        if not conditioned and line<lastrot and name in ('X','CX','CCX','SWAP','CSWAP'):
            targets=qs[-2:] if name in ('SWAP','CSWAP') else qs[-1:]
            for q in targets:
                if all_candidates or (line,q) in selected:
                    j=len(desc);desc.append({'kind':'candidate','line':line,'qubit':q});ops.append((10,q,j,0))
    assert not conditional_bad,conditional_bad
    desc.append({'kind':'phase_parity'})
    return ops,desc

def extract(tag,xs,selected=None,all_candidates=False):
    WORK.mkdir(exist_ok=True);ops,desc=parse(SOURCE,selected,all_candidates)
    (WORK/(tag+'.ops')).write_text('\n'.join(' '.join(map(str,o)) for o in ops))
    (WORK/(tag+'.json')).write_text(json.dumps(desc))
    (WORK/(tag+'.inputs')).write_text('\n'.join(map(str,xs)))
    cpp=WORK/'extract.cpp'
    if not cpp.exists():
        cpp.write_text(CPP);subprocess.run(['g++','-O3','-std=c++17',str(cpp),'-o',str(WORK/'extract')],check=True)
    subprocess.run([str(WORK/'extract'),str(WORK),tag,str(len(desc))],check=True)
    return load(tag)

def load(tag):
    desc=json.loads((WORK/(tag+'.json')).read_text());n=sum(1 for _ in open(WORK/(tag+'.inputs')));nw=(n+63)//64
    packed=np.memmap(WORK/(tag+'.u64'),mode='r',dtype='<u8',shape=(len(desc),nw))
    return desc,np.unpackbits(packed.view('u1'),axis=1,bitorder='little')[:,:n]

def phase(desc,bits,xs):
    value=np.zeros(len(xs),dtype=np.longdouble);ids=[];theta=[]
    for i,d in enumerate(desc):
        if d['kind']=='rotation':
            a=Fraction(d['half_turns'])/2;v=np.longdouble(a.numerator)/np.longdouble(a.denominator)
            value+=bits[i]*v
            if d['class']=='rotation':ids.append(i);theta.append(float(v/SCALE))
        elif d['kind']=='phase_parity':value+=bits[i]*np.longdouble(.5)
    goal=1/np.sqrt(np.array(xs,dtype=np.longdouble));err=value-goal;err-=np.rint(err)
    return np.array(err/SCALE,dtype=float),np.array(goal/(2**24*SCALE),dtype=float),ids,np.array(theta)

def lp(B,e,tol,drops,basecoef,new=None,active=None,iterations=1):
    A=B if new is None else np.column_stack((B,new));r=A.shape[1]
    active=np.arange(len(e)) if active is None else np.unique(active)
    bounds=[(-1e6,1e6)]*r+[(None,None)]
    for j in drops:bounds[j]=(-basecoef[j],-basecoef[j])
    for it in range(iterations):
        aa=np.array(A[active],dtype=float);lhs=np.column_stack((np.r_[aa,-aa],np.ones(2*len(active))))
        res=linprog(np.r_[np.zeros(r),-1],A_ub=lhs,b_ub=np.r_[tol[active]-e[active],tol[active]+e[active]],bounds=bounds,method='highs',options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
        if not res.success:return None
        delta=res.x[:-1];errs=e+A@delta; margins=tol-abs(errs);actual=float(margins.min());gap=float(res.x[-1]-actual)
        result={'margin_scaled':actual,'lp_margin_scaled':float(res.x[-1]),'gap':gap,'coef':delta.tolist(),'iterations':it+1,'active_size':len(active),'worst_x':int(np.argmin(margins))+1}
        if gap<1e-7:break
        worst=np.argpartition(margins,127)[:128];active=np.unique(np.r_[active,worst])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--top',type=int,default=80);p.add_argument('--full',type=int,default=12);args=p.parse_args();start=time.time()
    if not (WORK/'base.u64').exists():extract('base',range(1,N+1))
    desc,bits=load('base');e,tol,ids,theta=phase(desc,bits,np.arange(1,N+1));margin=tol-abs(e)
    active=np.unique(np.r_[np.arange(0,2048),np.linspace(0,N-1,4096,dtype=int),np.argpartition(margin,1024)[:1024],np.argpartition(margin[:100000],512)[:512]])
    if not (WORK/'sample.u64').exists():extract('sample',active+1,all_candidates=True)
    ds,bs=load('sample');es,ts,ri,th=phase(ds,bs,active+1);B=bs[ri].T;drop=int(np.argmin(abs(theta)))
    print(json.dumps({'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'baseline_margin':float(margin.min()*SCALE),'active':len(active),'candidate_snapshots':sum(x['kind']=='candidate' for x in ds),'drop':drop,'drop_line':desc[ids[drop]]['line']}),flush=True)
    # Rank by weighted least-squares residual after deleting the smallest angle.
    keep=[i for i in range(len(ri)) if i!=drop];w=1/np.maximum(ts,1.0);mat=np.asarray(B[:,keep],float)*w[:,None];goal=(-es+B[:,drop]*theta[drop])*w
    Q,_=np.linalg.qr(mat,mode='reduced');resid=goal-Q@(Q.T@goal)
    candidates=[];seen=set();existing={np.packbits(bs[i]).tobytes() for i in ri}
    for i,d in enumerate(ds):
        if d['kind']!='candidate':continue
        key=np.packbits(bs[i]).tobytes()
        if key in seen or key in existing:continue
        seen.add(key);v=np.asarray(bs[i],float)*w;v-=Q@(Q.T@v);norm=v@v
        if norm<1e-10:continue
        candidates.append((float((v@resid)**2/norm),i,d))
    candidates.sort(reverse=True,key=lambda x:x[0]);coarse=[]
    for c,i,d in candidates[:args.top]:
        rr=lp(B,es,ts,[drop],th,new=bs[i]);coarse.append({'candidate':d,'score':c,'result':rr})
    coarse.sort(key=lambda x:x['result']['margin_scaled'] if x['result'] else -1e100,reverse=True)
    (OUT/'invsqrt_next_phase_coarse.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'active_size':len(active),'unique_candidates':len(candidates),'drop_index':drop,'rows':coarse},indent=2))
    print(json.dumps({'coarse_best':coarse[:3],'elapsed':time.time()-start}),flush=True)
    selected=[(x['candidate']['line'],x['candidate']['qubit']) for x in coarse[:args.full]]
    df,bf=extract('finalists',range(1,N+1),selected=selected);ef,tf,rfi,thetaf=phase(df,bf,np.arange(1,N+1));BF=bf[rfi].T.copy();results=[]
    for row in coarse[:args.full]:
        d=row['candidate'];ii=next(i for i,x in enumerate(df) if x['kind']=='candidate' and x['line']==d['line'] and x['qubit']==d['qubit'])
        for mode,drops in [('replace',[drop]),('add',[])]:
            r=lp(BF,ef,tf,drops,thetaf,new=bf[ii],active=active,iterations=16)
            nrot=34-len(drops);m=r['margin_scaled']*SCALE if r else -1
            synth=nrot*(.56*np.log2(nrot/(np.pi*m))+5.3)/4 if m>0 else None
            results.append({'candidate':d,'mode':mode,'result':r,'rotation_count':nrot,'rotation_toffoli_equiv':synth})
            print(json.dumps({'candidate':d,'mode':mode,'margin':m,'synthesis':synth,'iterations':r['iterations'] if r else 0}),flush=True)
            (OUT/'invsqrt_next_phase_results.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'baseline_margin_turns':float(margin.min()*SCALE),'baseline_rotation_toffoli_equiv':231.2940713535,'baseline_arithmetic_cost_toffoli':1478.7500405453395,'qubits':46,'drop_index':drop,'rows':results,'elapsed':time.time()-start},indent=2))
    print('elapsed',time.time()-start,flush=True)

if __name__=='__main__':main()
