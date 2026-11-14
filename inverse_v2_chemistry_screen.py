"""Reference-free feasibility bounds and C43 initializations from a passing fit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'official_sources/Inzainos/verifiers'))
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors, reconstruct_x, lambda_h2


def h2_change_norm(x, y):
    """Accumulate directly in blocks to avoid cancellation in Gram traces."""
    x, y = x.reshape(-1, x.shape[-2] * x.shape[-1]), y.reshape(-1, y.shape[-2] * y.shape[-1])
    total = 0.0
    for lo in range(0, x.shape[1], 384):
        hi = min(x.shape[1], lo + 384)
        d = y[:, lo:hi].T @ y - x[:, lo:hi].T @ x
        total += np.einsum('ij,ij->', d, d)
    return float(np.sqrt(total))


def h2_coefs(data, brot):
    r, b, c = data['W'].shape
    u = reconstruct_u_vectors(data['angle_words'] / (1 << (brot - 1)), data['tree_edges'])
    return reconstruct_x(u[76:].reshape(r, b, 76), data['W'])


def c43_householder(data, x):
    out = dict(data)
    weights, identity, eigens, dropped, transforms = [], [], [], [], []
    for r in range(len(x)):
        xx = x[r].reshape(x.shape[1], -1)
        vals, vecs = np.linalg.eigh(xx @ xx.T)
        v = vecs[:, 0]
        j = int(np.argmax(np.abs(v)))
        e = np.zeros_like(v)
        e[j] = -np.copysign(1.0, v[j])
        u = v - e
        u /= np.linalg.norm(u)
        q = np.eye(len(v)) - 2 * np.outer(u, u)
        keep = [k for k in range(len(v)) if k != j]
        q = q[:, keep]
        weights.append(data['W'][r] @ q)
        identity.append(data['H2_I'][r] @ q)
        eigens.append(vals[:8].tolist())
        dropped.append({'r':r,'closest_column':j,'maximum_v_component':float(np.max(np.abs(v))),'norm_squared':float(vals[0])})
        transforms.append(q)
    out['W'], out['H2_I'] = np.array(weights), np.array(identity)
    return out, {'smallest_eigenvalues':eigens,'dropped_components':dropped}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--outdir',type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    source=ROOT/'dqi_inputs/chemistry_4033/submission.npz'
    data=dict(np.load(source));data.update(dict(np.load(source.with_name('asterios_refit.npz'))))
    base=h2_coefs(data,8)
    rows=[]
    for brot in (7,6):
        divisor=1<<(8-brot)
        for mode in ('floor','half_up','nearest_even'):
            dd=dict(data)
            if mode=='floor':words=data['angle_words']//divisor
            elif mode=='half_up':words=(data['angle_words']+divisor//2)//divisor
            else:words=np.rint(data['angle_words']/divisor).astype(np.int64)
            dd['angle_words']=words%(1<<brot)
            change=h2_change_norm(base,h2_coefs(dd,brot))
            row={'kind':f'brot{brot}_{mode}','h2_change_norm':change,'error2_lower_bound_from_passing_baseline':max(0,change-.020),'definitely_fails_at_fixed_W':change>.040}
            rows.append(row)
            print(json.dumps(row),flush=True)
    dd,detail=c43_householder(data,base)
    xx=h2_coefs(dd,8)
    change=h2_change_norm(base,xx)
    offset=data['H2_I']-data['W'].sum(1)
    newoffset=dd['H2_I']-dd['W'].sum(1)
    row={'kind':'C43_smallest_H2_component_householder','h2_change_norm':change,'error2_lower_bound_from_passing_baseline':max(0,change-.020),'definitely_fails_before_refit':change>.040,'lambda_h2_before':lambda_h2(data['W'],offset),'lambda_h2_after':lambda_h2(dd['W'],newoffset),**detail}
    rows.append(row);print(json.dumps(row),flush=True)
    np.savez_compressed(args.outdir/'c43_householder.npz',**dd)
    (args.outdir/'screen.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__=='__main__':main()
