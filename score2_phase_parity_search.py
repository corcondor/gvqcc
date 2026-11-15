#!/usr/bin/env python3
"""Dual-guided phase-polynomial column generation on the complete invsqrt domain.

Unlike the earlier one/two-wire screen, enumerate parities through weight five.
Each column is an existing simultaneous-wire parity and can be implemented by
CX/Z_POW/CX with no new Toffoli or qubits. Fixed Boolean-basis coefficient
optimization is a minimax LP, the small-error form of worst-case unitary distance.
The global phase is retained. Full-domain separation precedes candidate emission.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog
from invsqrt_structural_search import read_basis, MAX, SCALE

BASE_ROTATION_COST = 231.2940713535


def dot_blocked(matrix, coefficients):
    out = np.empty(len(matrix), dtype=float)
    for start in range(0, len(matrix), 32768):
        out[start:start+32768] = matrix[start:start+32768] @ coefficients
    return out


def fit(B, e, tol, initial, dropped, basecoef, new=None, iterations=18):
    matrix = B if new is None else np.column_stack((B, new))
    ncol = matrix.shape[1]
    bounds = [(-1e6, 1e6)]*ncol + [(None, None)]
    for j in dropped:
        bounds[j] = (-float(basecoef[j]), -float(basecoef[j]))
    objective = np.zeros(ncol+1)
    objective[-1] = -1
    active = np.unique(initial)
    for iteration in range(iterations):
        small = matrix[active].astype(float)
        A = np.column_stack((np.vstack((small, -small)), np.ones(2*len(active))))
        res = linprog(objective, A_ub=A, b_ub=np.r_[tol[active]-e[active], tol[active]+e[active]],
                      bounds=bounds, method='highs',
                      options={'dual_feasibility_tolerance':1e-8, 'primal_feasibility_tolerance':1e-8})
        if not res.success:
            return {'status':'LP_FAILED', 'message':res.message}, None, None
        err = e + dot_blocked(matrix, res.x[:-1])
        margins = tol - np.abs(err)
        margin = float(margins.min())
        gap = float(res.x[-1] - margin)
        dual = res.ineqlin.marginals[:len(active)] - res.ineqlin.marginals[len(active):]
        row = {'status':'CONVERGED' if gap<1e-7 else 'ITERATION_LIMIT',
               'margin_turns':margin*SCALE, 'upper_margin_turns':float(res.x[-1])*SCALE,
               'gap_turns':gap*SCALE, 'iterations':iteration+1,
               'active_constraints':len(active), 'coeff_scaled':res.x[:-1].tolist(),
               'max_error_ratio':float(np.max(np.abs(err)/tol)),
               'worst_x':int(np.argmin(margins))+1}
        if gap < 1e-7 or iteration == iterations-1:
            return row, active, dual
        bad = np.argpartition(margins, 127)[:128]
        active = np.unique(np.r_[active, bad])


def score_signatures(signatures, weights):
    out = np.zeros(len(signatures), dtype=float)
    for byte in range((len(weights)+7)//8):
        w = weights[8*byte:8*byte+8]
        lookup = np.zeros(256)
        for bit, weight in enumerate(w):
            lookup += ((np.arange(256) >> bit) & 1) * weight
        out += lookup[((signatures >> np.uint64(8*byte)) & np.uint64(255)).astype(np.uint8)]
    return out


def screen(desc, bits, active, dual, max_weight, retain):
    nz = np.flatnonzero(np.abs(dual)>1e-10)
    if len(nz)>64:
        raise RuntimeError(f'Dual support {len(nz)} exceeds exact signature width')
    witnesses, weights = active[nz], dual[nz]
    full_mask = (1 << len(nz))-1
    result = []
    seen = set()
    stats = []
    for line in (7705, 8075, 8189):
        ids = [i for i,d in enumerate(desc) if d['kind']=='snapshot' and d['line']==line]
        sigs = [sum(int(v)<<j for j,v in enumerate(bits[i,witnesses])) for i in ids]
        eligible=[]
        # Exact duplicate/complement columns on the entire domain are redundant.
        hashes=set()
        for q,i in enumerate(ids):
            if not bits[i].any() or bits[i].all():
                continue
            raw=np.packbits(bits[i],bitorder='little')
            h=hashlib.sha256(raw).digest()
            complement=hashlib.sha256(np.packbits(1-bits[i],bitorder='little')).digest()
            if h in hashes or complement in hashes:
                continue
            hashes.add(h);eligible.append(q)
        total=0
        for size in range(1,max_weight+1):
            combos=list(itertools.combinations(eligible,size))
            if not combos:continue
            signatures=np.fromiter((np.bitwise_xor.reduce([np.uint64(sigs[q]) for q in c]) for c in combos),dtype=np.uint64,count=len(combos))
            score=score_signatures(signatures,weights)
            positive=np.abs(score)
            negative=np.abs(float(weights.sum())-score)
            values=np.maximum(positive,negative)
            top=np.argsort(-values)[:retain*8]
            total+=len(combos)
            for k in top:
                qubits=combos[int(k)]
                negate=bool(negative[k]>positive[k])
                signature=int(signatures[k])^(full_mask if negate else 0)
                if not signature or signature==full_mask or signature in seen:
                    continue
                seen.add(signature)
                result.append({'line':line,'qubits':list(qubits),'negate':negate,
                               'basis_indices':[ids[q] for q in qubits],
                               'dual_correlation':float(values[k]),'signature':str(signature)})
        stats.append({'line':line,'eligible_wire_functions':len(eligible),'parities_screened':total})
    result.sort(key=lambda row:-row['dual_correlation'])
    return result[:retain], {'dual_support':len(nz),'witness_x':(witnesses+1).tolist(),
                            'dual_weights':weights.tolist(),'snapshots':stats}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-weight',type=int,default=5)
    p.add_argument('--candidates',type=int,default=12)
    p.add_argument('--seconds',type=float,default=360)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    start=time.monotonic()
    desc,bits,idx,e,tol=read_basis()
    B=bits[idx].T.copy()
    basecoef=np.array([float(Fraction(desc[i]['half_turns'])/2)/SCALE for i in idx])
    margin=tol-np.abs(e)
    active=np.unique(np.r_[np.arange(2048),np.linspace(0,MAX-1,2048,dtype=int),np.argpartition(margin,2048)[:2048]])
    small=list(map(int,np.argsort(np.abs(basecoef))[:4]))
    scenarios=[tuple(small[:1]),tuple(small[:2]),tuple()]
    report={'status':'RUNNING','source_kmb_sha256':'e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6',
            'domain':MAX,'max_parity_weight':args.max_weight,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'baseline_rotation_cost':BASE_ROTATION_COST,'experiments':[],
            'method':'Dual-guided XOR parity columns; exact deterministic full-domain LP separation; no sampled-score objective',
            'official_verified':False,'scenarios':[]}
    def save():
        report['seconds']=time.monotonic()-start
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,indent=2)+'\n')
    for dropped in scenarios:
        if time.monotonic()-start>args.seconds:break
        initial,aa,dual=fit(B,e,tol,active,dropped,basecoef)
        print(json.dumps({'drop':dropped,'base_fit':{k:v for k,v in initial.items() if k!='coeff_scaled'}}),flush=True)
        if aa is None:continue
        candidates,screen_stats=screen(desc,bits,aa,dual,args.max_weight,args.candidates)
        report['scenarios'].append({'drop':dropped,'initial_fit':initial,'screen':screen_stats,'candidates':candidates})
        save()
        print(json.dumps({'drop':dropped,'screen':screen_stats,'top':candidates[:3]}),flush=True)
        for candidate in candidates:
            if time.monotonic()-start>args.seconds:break
            new=np.full(MAX,int(candidate['negate']),dtype=np.uint8)
            for i in candidate['basis_indices']:new^=bits[i]
            # Avoid spending a new rotation on an unchanged old rotation function.
            if any(np.array_equal(new,bits[i]) for i in idx):
                continue
            rr,_,_=fit(B,e,tol,aa,dropped,basecoef,new)
            nrot=len(idx)-len(dropped)+1
            row={'drop':dropped,'candidate':candidate,'fit':rr,'generic_rotations':nrot}
            m=rr.get('margin_turns',-1)
            if m>0:
                row['predicted_rotation_cost']=float(nrot*(.56*np.log2(nrot/(np.pi*m))+5.3)/4)
                row['predicted_rotation_cost_delta']=row['predicted_rotation_cost']-BASE_ROTATION_COST
            report['experiments'].append(row);save()
            print(json.dumps({'drop':dropped,'parity':candidate['qubits'],'line':candidate['line'],'negate':candidate['negate'],
                              'margin':m,'cost':row.get('predicted_rotation_cost'),'status':rr['status']}),flush=True)
    report['status']='FINISHED'
    report['improving_predictions']=[i for i,row in enumerate(report['experiments']) if row.get('predicted_rotation_cost_delta',1)<0]
    save()
    print(json.dumps({'status':report['status'],'experiments':len(report['experiments']),
                      'improving_predictions':report['improving_predictions'],'seconds':report['seconds']}),flush=True)


if __name__=='__main__':main()
