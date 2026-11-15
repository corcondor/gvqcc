#!/usr/bin/env python3
"""Dual spectral bound for the intersection of group locality and total PSD rank."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import block_diag, eigh, solve_triangular
from scipy.sparse.linalg import LinearOperator, cg


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projection', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--rank', type=int, default=40)
    p.add_argument('--iterations', type=int, default=2)
    p.add_argument('--save-dual', type=Path)
    a = p.parse_args()
    proj = dict(np.load(a.projection, allow_pickle=False))
    s = proj['target']
    f = proj['features']
    r, b = int(proj['group_count']), int(proj['group_size'])
    k = r * a.rank
    g = proj['gram'].reshape(r,b,r,b).transpose(0,2,1,3)
    identity = np.eye(r*b)
    finv = solve_triangular(f, identity, lower=False, check_finite=False)

    def normal(flat):
        groups = flat.reshape(r,b,b)
        out = np.zeros_like(groups)
        for i in range(r):
            for j in range(r):
                cross=g[i,j]
                out[i] += cross @ groups[j] @ cross.T
        return out.ravel()

    def blocks(mat):
        return np.array([mat[i*b:(i+1)*b, i*b:(i+1)*b] for i in range(r)])

    def rank_project(mat):
        ev, vec = eigh(mat, subset_by_index=[r*b-k,r*b-1], check_finite=False)
        ev = np.maximum(ev,0.)
        return np.sum(ev**2), (vec*ev) @ vec.T

    linear = LinearOperator((r*b*b,r*b*b), matvec=normal, dtype=np.float64)
    extra = np.zeros_like(s)
    top_value, top = rank_project(s)
    s2=np.sum(s*s)
    rows=[]
    for iteration in range(a.iterations):
        rhs = blocks(f.T @ top @ f).ravel()
        coeff, status = cg(linear,rhs,rtol=1e-10,atol=1e-14,maxiter=1000)
        approx = top-f@block_diag(*coeff.reshape(r,b,b))@f.T
        leakage=blocks(f.T @ approx @ f)
        # Regardless of the iterative solve's residual, remove every diagonal
        # block of f^T approx f explicitly.  This keeps the dual variable in
        # the exact annihilator of the grouped linear space in real arithmetic.
        correction=finv.T @ block_diag(*leakage) @ finv
        direction = approx-correction
        assert np.linalg.norm(blocks(f.T @ direction @ f)) < 1e-8
        original_value=top_value
        trial_rows=[]
        for scale in (.125,.25,.5,1.,2.):
            proposal=extra-scale*direction
            squares, projected=rank_project(s+proposal)
            trial_rows.append(dict(scale=scale, top_rank_energy=squares))
            if squares < top_value:
                best=(proposal,projected)
                top_value=squares
        if top_value < original_value:
            extra,top=best
        distance=max(0., np.sqrt(max(0.,s2-top_value))-float(proj['uncertainty']))
        error=np.sqrt(float(proj['outside_lower'])+distance**2)
        row=dict(iteration=iteration+1, cg_status=status, projected_direction_norm=float(np.linalg.norm(direction)),
                 exact_correction_norm=float(np.linalg.norm(correction)),
                 dual_group_overlap=float(np.linalg.norm(blocks(f.T @ extra @ f))),
                 energy_gain=float(original_value-top_value), error2_lower_bound=error,
                 trial_rows=trial_rows)
        rows.append(row)
        print(json.dumps(row),flush=True)
        if error > .0201:
            break
    if a.save_dual:
        np.savez(a.save_dual, dual=extra)
    a.out.write_text(json.dumps(dict(C=a.rank, records=rows,
       scope='Numerical necessary condition in exact fixed word grouping. Bound follows from orthogonal dual matrices and PSD rank relaxation.'),indent=2)+'\n')


if __name__ == '__main__':
    main()
