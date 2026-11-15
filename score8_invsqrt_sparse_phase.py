#!/usr/bin/env python3
"""Approximate fixed-feature Clifford/T lattice exclusion and sparse refit.

The integer left inverse used for exact modular equivalence also gives a
rigorous approximate bound. If baseline and candidate are both valid, then
each phase coefficient changes by at most sum |B_ji|*(2*tolerance_i), modulo
an integer turn. This safely prunes distant Clifford/T lattice targets; it
does not assume the approximate optimization must preserve exact phases.
Remaining generic rotations are forced individually to the nearest T lattice
and all other generic coefficients are minimax refit over every legal input.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog

MAX=3133452
SCALE=1e-11
ROOT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matvec(B,c):
    y=np.empty(len(B))
    for i in range(0,len(B),32768):y[i:i+32768]=B[i:i+32768]@c
    return y


def load(work):
    desc=json.loads((work/'basis.json').read_text())['basis'];nw=(MAX+63)//64
    arr=np.memmap(work/'basis.u64',mode='r',dtype='<u8',shape=(len(desc),nw))
    ix=[i for i,d in enumerate(desc) if d['kind'] in ('rotation','phase_parity')]
    bits=np.unpackbits(np.asarray(arr[ix]).view('u1'),axis=1,bitorder='little')[:,:MAX]
    dd=[desc[i] for i in ix];phase=np.zeros(MAX,dtype=np.longdouble)
    for b,d in zip(bits,dd):
        f=Fraction(d['half_turns'])/2 if d['kind']=='rotation' else Fraction(1,2)
        phase+=b*(np.longdouble(f.numerator)/np.longdouble(f.denominator))
    x=np.arange(1,MAX+1,dtype=np.longdouble);target=1/np.sqrt(x);tol=target/(1<<24)
    err=phase-target;err-=np.rint(err)
    generic=[i for i,d in enumerate(dd) if d.get('class')=='rotation']
    return bits[generic].T.copy(),np.asarray(err/SCALE,dtype=float),np.asarray(tol/SCALE,dtype=float),[dd[i] for i in generic]


def fit(B,e,t,index,adjustment,baseactive):
    active=np.array(baseactive);r=B.shape[1];obj=np.zeros(r+1);obj[-1]=-1
    bounds=[(-2e5,2e5)]*r+[(None,None)];bounds[index]=(adjustment,adjustment)
    for iteration in range(30):
        a=np.asarray(B[active],dtype=float)
        res=linprog(obj,A_ub=np.column_stack((np.vstack((a,-a)),np.ones(2*len(active)))),b_ub=np.r_[t[active]-e[active],t[active]+e[active]],bounds=bounds,method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        if not res.success:return {'status':'LP_FAILED','message':res.message}
        err=e+matvec(B,res.x[:-1]);m=t-abs(err);mn=float(m.min());gap=float(res.x[-1]-mn)
        row={'status':'CONVERGED' if gap<1e-7 else 'ITERATING','min_margin_turns':mn*SCALE,'lp_margin_turns':float(res.x[-1])*SCALE,'gap_turns':gap*SCALE,'max_error_ratio':float(np.max(abs(err)/t)),'worst_x':int(np.argmin(m))+1,'iterations':iteration+1,'coeff_adjustment_scaled':res.x[:-1].tolist()}
        if gap<1e-7:return row
        worst=np.argpartition(m,128)[:128];active=np.unique(np.r_[active,worst])
    return row


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--work',type=Path,default=ROOT.parent/'invsqrt_structural_work')
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    certpath=ROOT/'score6_invsqrt_modular_certificate.json';cert=json.loads(certpath.read_text())
    xs=cert['witness_xs'];left=cert['integer_left_inverse'];rows=[];possible=[]
    for j,f in enumerate(cert['features']):
        angle=Fraction(f['half_turns'])/2;nearest=Fraction(round(angle*8),8);distance=abs(angle-nearest)
        bound=sum(abs(b)*2*Fraction(math.isqrt((1<<130)//x)>>25,1<<64) for b,x in zip(left[j+1],xs))
        row={'feature_index':j,'line':f['line'],'kind':f['kind'],'angle_turns':str(angle),'nearest_T_lattice_turns':str(nearest),'distance_turns':str(distance),'approximate_bound_turns':str(bound),'excluded':bool(distance>bound)}
        rows.append(row)
        if f['kind']=='rotation' and distance<=bound:possible.append(row)
    report={'source_kmx_sha256':cert['source_sha256'],'certificate_sha256':sha(certpath),'fixed_phase_features':38,'generic_rotations':33,'rigorous_approximate_lattice_checks':rows,'generic_targets_excluded':sum(x['kind']=='rotation' and x['excluded'] for x in rows),'candidate_targets_for_LP':len(possible),'LP':[],'full_domain_inputs':MAX,'baseline_cost':78673.55534364567,'scope':'Same 38 Boolean predicates. Five originally Clifford/T coefficients are fixed to preserve their rotation class. Integer-left-inverse bounds include an arbitrary constant phase. Numerical LP uses float64 constraints and longdouble baseline phase; an improving candidate still requires exact integer oracle and native verification.'}
    print(json.dumps({k:report[k] for k in ('generic_targets_excluded','candidate_targets_for_LP')}),flush=True)
    B,e,t,generic=load(a.work);margin=t-abs(e)
    active=np.unique(np.r_[np.arange(2048),np.linspace(0,MAX-1,2048,dtype=int),np.argpartition(margin,1024)[:1024]])
    by_angle={Fraction(d['half_turns'])/2:i for i,d in enumerate(generic)}
    for item in possible:
        angle=Fraction(item['angle_turns']);nearest=Fraction(item['nearest_T_lattice_turns']);index=by_angle[angle]
        result=fit(B,e,t,index,float((nearest-angle)/Fraction(str(SCALE))),active)
        row={**item,'generic_index':index,'fit':result}
        if result.get('min_margin_turns',0)>0:
            m=result['min_margin_turns'];nrot=32;tcost=nrot*(.56*math.log2(nrot/(math.pi*m))+5.3)/4
            if nearest%Fraction(1,4):tcost+=.25
            row['predicted_cost']=46*(1478.7506100300882+.25+tcost)
        report['LP'].append(row);report['seconds']=time.monotonic()-begin
        (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'feature_index':item['feature_index'],'generic_index':index,'line':item['line'],'margin':result.get('min_margin_turns'),'cost':row.get('predicted_cost'),'status':result['status'],'seconds':report['seconds']}),flush=True)
    report['improving_candidates']=[r['feature_index'] for r in report['LP'] if r.get('predicted_cost',math.inf)<report['baseline_cost']]
    report['seconds']=time.monotonic()-begin
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'improving_candidates':report['improving_candidates'],'seconds':report['seconds']}),flush=True)


if __name__=='__main__':main()
