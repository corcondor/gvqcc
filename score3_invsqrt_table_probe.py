#!/usr/bin/env python3
"""Integer-table + drop-q41 numerical probes of actual e46 predicates.

NOT a candidate circuit: only the forward arithmetic/rotation predicates are
changed. A positive numerical result would still need two loaders, reversible
uncompute, every measurement branch and the official integer oracle checked.
The 64-row private generator is unavailable; this extracts its exact values
from the existing circuit and independently checks its six signed-row formula.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,time
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from score_invsqrt_retire import advance

ROOT=Path(__file__).resolve().parent
MAX=3133452
SCALE=1e-11
PIN='69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1'
DWIRES=[34,36,30,32,28,35,33,31,29,26,27,37,38]
SWIRES=[21,39,40,41,42,37,38]

def write_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def coefficient_values(A,S):
    v=np.arange(4096,dtype=np.int64);a=v>>6;s=np.asarray(S,dtype=np.int64)[a]
    d=np.asarray(A,dtype=np.int64)[a].copy()
    for i in range(6):
        high=s>>(6-i)
        plus=high+((s>>(5-i))&1)
        minus=high+(((s>>(4-i))&1) if i<5 else 0)
        d+=np.where((v>>i)&1,-minus,plus)
    return (d&8191).astype('<u2')

def packing_violations(A,S):
    """Rows incompatible with the existing D-high/S-high shared-wire chart."""
    bad=[]
    for a,(aa,ss) in enumerate(zip(A,S)):
        a10=(aa>>10)&1;a11=(aa>>11)&1;a12=(aa>>12)&1;s4=(ss>>4)&1
        s6=a12^1^a10^a11^(a10&a11)
        s5=a11^1^a10^((a10^s6)&(s4^s6))
        f=((a>>0)^(a>>1)^(a>>2)^(a>>5))&1
        f^=(((a>>0)^(a>>2))&1)&((a>>4)&1)
        s0=f^a12^s6^s5
        if (s0!=(ss&1) or s5!=((ss>>5)&1) or s6!=((ss>>6)&1)):bad.append(a)
    return bad

def extract_table(lines):
    n=4096;one=(1<<n)-1;q=[0]*46
    for j in range(12):q[10+j]=sum(((v>>j)&1)<<v for v in range(n))
    snaps={}
    for i in range(1661,3318):
        w=lines[i].split();op=w[0];qs=tuple(map(int,re.findall(r'\bq(\d+)\b',lines[i])))
        assert op not in ('PUSH_CONDITION','POP_CONDITION')
        advance(op,qs,q,one)
        if i+1 in (2889,2909,3318):snaps[i+1]=q.copy()
    def decode(state,wires):
        return np.array([sum(((state[z]>>v)&1)<<j for j,z in enumerate(wires)) for v in range(n)],dtype=np.int64)
    aa=decode(snaps[2889],DWIRES).reshape(64,64)
    ss=decode(snaps[2909],SWIRES).reshape(64,64)
    assert np.all(aa==aa[:,:1]) and np.all(ss==ss[:,:1])
    A=aa[:,0];S=ss[:,0];actual=decode(snaps[3318],DWIRES)
    predicted=coefficient_values(A,S);assert np.array_equal(actual,predicted)
    assert not packing_violations(A,S)
    return {'A':A.tolist(),'S':S.tolist(),'D':actual.tolist(),
            'addresses':64,'raw_root_values':4096,'address_wires':list(range(16,22)),
            'D_wires_after_line3318':DWIRES,'S_wires_after_line2909':SWIRES,
            'exact_signed_row_formula_matches_all4096':True,
            'shared_wire_chart_bad_rows':packing_violations(A,S),
            'first_loader_CCX':sum(s.startswith('CCX ') for s in lines[1661:2889]),
            'first_loader_HMR':sum(s.startswith('HMR ') for s in lines[1661:2889]),
            'note':'H high bits share physical storage with D; arbitrary new tables still require a valid loader/cleanup implementation.'}

def operations(lines,drop):
    ops=[];basis=[];active=[True];bits={}
    types={'X':0,'CX':1,'CCX':2,'SWAP':3,'CSWAP':4,'HMR':5,'Z':6,'CZ':7,'CCZ':8,'NEG':9}
    # The last fractional rotation is line8318, but line8346 has the final
    # active all-zero-branch Clifford phase CZ(q23,q25). Include it as well.
    for lineno,line in enumerate(lines[:8346],1):
        if lineno==1662:ops.append((12,0,0,0))
        if lineno==3319:ops.append((13,0,0,0))
        if lineno==7601 and drop:ops.append((5,41,0,0))
        w=line.split();name=w[0]
        if name=='PUSH_CONDITION':active.append(active[-1] and bits.get(int(w[-1][1:]),False));continue
        if name=='POP_CONDITION':active.pop();continue
        enabled=active[-1]
        if 'if' in w:enabled=enabled and bits.get(int(w[w.index('if')+1][1:]),False);w=w[:w.index('if')]
        if not enabled:continue
        if name in ('APPEND_TO_REGISTER','REGISTER'):continue
        if name=='HMR':bits[int(w[2][1:])]=False
        if name=='BIT_STORE0':bits[int(w[1][1:])]=False;continue
        if name=='BIT_INVERT':k=int(w[1][1:]);bits[k]=not bits.get(k,False);continue
        if name=='Z_POW':
            f=Fraction(w[2]);j=len(basis)
            basis.append({'kind':'rotation','line':lineno,'qubit':int(w[1][1:]),'half_turns':str(f),
                          'class':'clifford' if f%Fraction(1,2)==0 else 't' if f%Fraction(1,4)==0 else 'rotation'})
            ops.append((10,int(w[1][1:]),j,0));continue
        if name not in types:raise ValueError((lineno,w))
        qs=[int(s[1:]) for s in w[1:] if s.startswith('q')]
        ops.append(tuple([types[name]]+qs+[0]*(3-len(qs))))
    basis.append({'kind':'phase_parity','line':8346})
    return ops,basis

def read_phase(prefix,desc,n=MAX,xs=None):
    nw=(n+63)//64;packed=np.memmap(str(prefix)+'.basis.u64',mode='r',dtype='<u8',shape=(len(desc),nw))
    bits=np.unpackbits(np.asarray(packed).view('u1'),axis=1,bitorder='little')[:,:n]
    phase=np.zeros(n,dtype=np.longdouble)
    for b,d in zip(bits,desc):
        f=Fraction(d['half_turns'])/2 if d['kind']=='rotation' else Fraction(1,2)
        phase+=b*(np.longdouble(f.numerator)/np.longdouble(f.denominator))
    x=np.arange(1,n+1,dtype=np.longdouble) if xs is None else np.asarray(xs,dtype=np.longdouble)
    target=1/np.sqrt(x);tol=target/2**24
    err=phase-target;err-=np.rint(err)
    ix=[i for i,d in enumerate(desc) if d.get('class')=='rotation']
    return bits[ix].T.copy(),np.asarray(err/SCALE,dtype=float),np.asarray(tol/SCALE,dtype=float)

def dot(B,c):
    out=np.empty(len(B))
    for i in range(0,len(B),32768):out[i:i+32768]=B[i:i+32768]@c
    return out

def fit(B,e,t,maxiter=15):
    n=len(B);margin=t-abs(e)
    active=np.unique(np.r_[np.arange(min(n,2048)),np.linspace(0,n-1,min(n,2048),dtype=int),np.argsort(margin)[:min(n,1024)]])
    obj=np.zeros(B.shape[1]+1);obj[-1]=-1
    for it in range(maxiter):
        a=np.asarray(B[active],dtype=float);mat=np.column_stack((np.vstack((a,-a)),np.ones(2*len(active))))
        res=linprog(obj,A_ub=mat,b_ub=np.r_[t[active]-e[active],t[active]+e[active]],
                    bounds=[(-1e6,1e6)]*B.shape[1]+[(None,None)],method='highs',
                    options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        if not res.success:return {'success':False,'message':res.message},None,None
        err=e+dot(B,res.x[:-1]);m=t-abs(err);worst=np.argpartition(m,min(127,n-1))[:min(128,n)]
        result={'success':True,'margin_turns':float(m.min()*SCALE),'lp_margin_turns':float(res.x[-1]*SCALE),
                'max_error_ratio':float(np.max(abs(err)/t)),'worst_x':int(np.argmax(abs(err)/t))+1,
                'negative_margin_inputs':int(np.count_nonzero(m<0)),'iterations':it+1,
                'gap_turns':float((res.x[-1]-m.min())*SCALE),'coeff_adjustment_scaled':res.x[:-1].tolist()}
        if res.x[-1]-m.min()<1e-7:return result,err,active
        active=np.unique(np.r_[active,worst])
    return result,err,active

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('baseline','probe'),default='baseline')
    p.add_argument('--rows',type=int,nargs='*',default=[]);p.add_argument('--limit',type=int,default=8)
    p.add_argument('--joint',action='store_true',help='The four joint A/S +/-1 corners per row, instead of axial updates.')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    source=ROOT/'invsqrt_structural_e46.kmx';assert sha(source)==PIN
    lines=source.read_text().splitlines();table=extract_table(lines)
    write_json(a.out/'table.json',table)
    baseD=coefficient_values(table['A'],table['S']);baseD.tofile(a.out/'base_D.u16')
    ops,desc=operations(lines,True)
    (a.out/'ops.txt').write_text('\n'.join(' '.join(map(str,x)) for x in ops)+'\n')
    write_json(a.out/'basis.json',{'basis':desc,'scope':'forward prefix only, all-zero HMR branch; numerical intervention'})
    executable=a.out/'extract'
    subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'score3_invsqrt_table_extract.cpp'),'-o',str(executable)],check=True)
    def extract(name,d):
        path=a.out/(name+'_D.u16');d.tofile(path);prefix=a.out/name
        receipt=subprocess.run([str(executable),str(a.out/'ops.txt'),str(a.out/'base_D.u16'),str(path),str(prefix),str(len(desc)),'all'],check=True,capture_output=True,text=True)
        return prefix,json.loads(receipt.stdout)
    if a.mode=='baseline':
        prefix,receipt=extract('baseline_drop1',baseD)
        B,e,t=read_phase(prefix,desc);fitrow,err,active=fit(B,e,t)
        roots=np.fromfile(str(prefix)+'.roots.u16',dtype='<u2');rows=roots>>6;groups=[]
        for row in range(64):
            ids=np.flatnonzero(rows==row);bad=ids[np.abs(err[ids])>t[ids]]
            worst=ids[np.argmax(np.abs(err[ids])/t[ids])]
            groups.append({'row':row,'A':table['A'][row],'S':table['S'][row],'inputs':len(ids),'failing_inputs':len(bad),
                           'worst_x':int(worst)+1,'max_error_ratio':float(abs(err[worst])/t[worst]),
                           'minimum_margin_turns':float(np.min(t[ids]-abs(err[ids]))*SCALE)})
        result={'status':'NUMERICAL_PROBE_ONLY','source_kmx_sha256':PIN,'phase_drop_wire':41,'extraction':receipt,'fit':fitrow,
                'by_table_row':groups,'max_failure_rows':sorted(groups,key=lambda x:-x['failing_inputs']),
                'full_circuit_verified':False,'seconds':time.monotonic()-begin}
        write_json(a.out/'baseline.json',result);np.save(a.out/'baseline_active.npy',active)
        print(json.dumps({**{k:v for k,v in result.items() if k not in ('by_table_row','max_failure_rows')},'worst_rows':result['max_failure_rows'][:8]}),flush=True)
    else:
        old=json.loads((a.out/'baseline.json').read_text());rows=a.rows or [x['row'] for x in old['max_failure_rows'][:2]]
        trials=[];suffix='joint' if a.joint else 'probes'
        deltas=[(da,ds) for da in (-1,1) for ds in (-1,1)] if a.joint else [(-1,0),(1,0),(0,-1),(0,1)]
        planned=[(row,da,ds) for row in rows for da,ds in deltas][:a.limit]
        for row,da,ds in planned:
            aa=list(table['A']);ss=list(table['S']);aa[row]+=da;ss[row]+=ds
            if not 0<=ss[row]<128 or not 0<=aa[row]<8192:continue
            label=f'row{row}_A{da:+d}_S{ds:+d}'.replace('+','p').replace('-','m')
            prefix,receipt=extract(label,coefficient_values(aa,ss));B,e,t=read_phase(prefix,desc)
            fitrow,_,_=fit(B,e,t)
            record={'row':row,'delta_A':da,'delta_S':ds,'name':label,'extract':receipt,'fit':fitrow,
                    'changed_integer_coefficients':int(bool(da))+int(bool(ds)),
                    'existing_shared_wire_chart_bad_rows':packing_violations(aa,ss),
                    'full_circuit_verified':False,'seconds_total':time.monotonic()-begin}
            trials.append(record);write_json(a.out/(suffix+'.json'),{'scope':'numerical forward intervention, not a submitted circuit','baseline':old['fit'],'trials':trials})
            print(json.dumps(record),flush=True);del B,e,t
        write_json(a.out/(suffix+'_summary.json'),{'status':'COMPLETE_BOUNDED_NUMERICAL_PROBE','source_kmx_sha256':PIN,'tested_rows':rows,
                    'trials':trials,'feasible_count':sum(x['fit']['success'] and x['fit']['margin_turns']>0 for x in trials),
                    'full_circuit_verified':False,'seconds':time.monotonic()-begin})

if __name__=='__main__':main()
