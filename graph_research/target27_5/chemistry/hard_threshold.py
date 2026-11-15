#!/usr/bin/env python3
"""Project the quadratic DF-THC Gram objective directly onto capped PSD rank."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import eigh, solve_triangular

from chem_next_fixed_angles import FastFixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--npz', type=Path, required=True)
    p.add_argument('--words', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=40.)
    p.add_argument('--ranks', type=int, nargs='+', default=[40, 43])
    a = p.parse_args()
    data = dict(np.load(a.npz, allow_pickle=False))
    words = np.load(a.words, allow_pickle=False)[:1220].astype(np.uint8)
    assert hashlib.sha256(words.tobytes()).hexdigest() == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    data['angle_words'] = words
    m = FastFixedAngles(data)
    r, b, c = data['W'].shape
    ls = np.array([np.linalg.cholesky(m.G4[i, i]) for i in range(r)])
    qs = np.array([solve_triangular(ls[i], m.V[i*b:(i+1)*b], lower=True) for i in range(r)])
    cross = np.array([[qs[i] @ qs[j].T for j in range(r)] for i in range(r)])
    lipschitz_bound = np.linalg.eigvalsh(np.array(
        [[np.linalg.norm(cross[i][j], ord=2)**2 for j in range(r)] for i in range(r)]))[-1]
    y0 = ls.transpose(0, 2, 1) @ data['W']
    p0 = y0 @ y0.transpose(0, 2, 1)
    coeff = []
    for i in range(r):
        g = solve_triangular(ls[i], m.A[i], lower=True)
        coeff.append(solve_triangular(ls[i], g.T, lower=True).T)
    coeff = np.array(coeff)

    def f_g(mats):
        dif = mats - p0
        prod = np.zeros_like(coeff)
        for i in range(r):
            for j in range(r):
                g = cross[i, j]
                prod[i] += g @ dif[j] @ g.T
        err = m.e20 + np.sum((2*coeff + prod) * dif)
        return float(err), coeff + prod

    def project(mats, rank):
        pieces = []
        for i in range(r):
            ev, vec = eigh(mats[i], subset_by_index=[b-rank, b-1], check_finite=False)
            pieces.append(vec * np.sqrt(np.maximum(ev, 0.))[None, :])
        factors = np.array(pieces)
        return factors @ factors.transpose(0, 2, 1), factors

    results = []
    # Warm-start with a convex rank-unrestricted fit first.  Each stage is
    # accepted by its real weighted quadratic merit, including acceleration.
    warm = p0
    for rank in [b] + a.ranks:
        start = time.monotonic()
        point, best_factors = project(warm, rank)
        value, deriv = f_g(point)
        initial = np.sqrt(value)
        previous = point
        accel = 1.0
        total = 0
        accepted = 0
        step = 1. / lipschitz_bound
        while time.monotonic() - start < a.seconds:
            next_accel = (1 + np.sqrt(1+4*accel*accel))/2
            probe = point + (accel-1.)/next_accel * (point-previous)
            probe_value, probe_derivative = f_g(probe)
            proposal, factors = project(probe-step*probe_derivative, rank)
            new_value, new_derivative = f_g(proposal)
            total += 1
            if new_value > value:
                # A genuine merit test, with a restart on the current point.
                proposal, factors = project(point-step*deriv, rank)
                new_value, new_derivative = f_g(proposal)
                next_accel = 1.
            if new_value <= value:
                previous, point = point, proposal
                value, deriv = new_value, new_derivative
                best_factors = factors
                accel = next_accel
                accepted += 1
            else:
                step *= .5
                accel = 1.
            if step < 1e-10:
                break
        if rank == b:
            warm = point
            row = dict(rank=rank, initial_error2=initial, final_error2=np.sqrt(value),
                       iterations=total, accepted=accepted, seconds=time.monotonic()-start)
        else:
            w = np.array([solve_triangular(ls[i].T, best_factors[i], lower=False) for i in range(r)])
            d0 = data['H2_I'] - data['W'].sum(axis=1)
            target = np.einsum('rbc,rc,rbd->d', data['W'], d0, m.V.reshape(r, b, -1), optimize=True)
            design = np.einsum('rbc,rbd->rcd', w, m.V.reshape(r,b,-1), optimize=True).reshape(r*rank,-1).T
            d = np.linalg.lstsq(design, target, rcond=1e-12)[0].reshape(r,rank)
            official = evaluate_dfthc_angle_words(words,w,d,m.S,m.beta,m.ref,
                    brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
            assert abs(official['error_2']-np.sqrt(value)) < 1e-9
            row = dict(rank=rank, initial_error2=initial, final_error2=np.sqrt(value),
                       iterations=total, accepted=accepted, seconds=time.monotonic()-start,
                       official_metrics=official)
            arrays = dict(data)
            arrays['W'] = w
            arrays['H2_I'] = d+w.sum(axis=1)
            np.savez_compressed(a.out.with_name(f'hard_c{rank}.npz'), **arrays)
        results.append(row)
        print(json.dumps(row), flush=True)
    report = dict(status='PROJECTED_GRAM_SEARCH_COMPLETE', lipschitz_upper_bound=lipschitz_bound,
                  npz_sha256=hashlib.sha256(a.npz.read_bytes()).hexdigest(), results=results)
    a.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
