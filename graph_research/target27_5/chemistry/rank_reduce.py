#!/usr/bin/env python3
"""Fit reduced ensemble rank in orthonormal projector coordinates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import minimize
from chem_next_fixed_angles import FastFixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--npz", required=True, type=Path)
    p.add_argument("--words", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--rank", default=40, type=int)
    p.add_argument("--seconds", default=40, type=float)
    p.add_argument("--refit-from", type=Path)
    a = p.parse_args()

    base = dict(np.load(a.npz, allow_pickle=False))
    words = np.load(a.words, allow_pickle=False)[:1220, :75].astype(np.uint8)
    digest = hashlib.sha256(words.tobytes()).hexdigest()
    assert digest == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    base["angle_words"] = words
    model = FastFixedAngles(base)
    orig_w = base["W"]
    r, b, prev_c = orig_w.shape
    c = a.rank
    assert 1 <= c < prev_c
    orig_d = base["H2_I"] - orig_w.sum(axis=1)

    ls = np.array([np.linalg.cholesky(model.G4[i, i]) for i in range(r)])
    qs = np.array([solve_triangular(ls[i], model.V[i*b:(i+1)*b], lower=True)
                   for i in range(r)])
    cross = np.array([[qs[i] @ qs[j].T for j in range(r)] for i in range(r)])
    # All projections of the original residual use the same Frobenius metric.
    gradients = []
    for i in range(r):
        left = solve_triangular(ls[i], model.A[i], lower=True)
        gradients.append(solve_triangular(ls[i], left.T, lower=True).T)
    gradients = np.array(gradients)
    y0 = ls.transpose(0, 2, 1) @ orig_w
    p0 = y0 @ y0.transpose(0, 2, 1)
    # Orthogonal rotation within each rho, then remove the smallest terms
    # by their actual squared Frobenius weight.
    right_bases = [np.linalg.svd(y0[i], full_matrices=False)[2].T[:, :c] for i in range(r)]
    y = np.array([y0[i] @ right_bases[i] for i in range(r)])
    if a.refit_from:
        other = dict(np.load(a.refit_from, allow_pickle=False))
        assert np.array_equal(other["angle_words"], words)
        y = ls.transpose(0, 2, 1) @ other["W"]
    initial_d = np.array([orig_d[i] @ right_bases[i] for i in range(r)])

    start = time.monotonic()
    latest = y.ravel()
    best = latest.copy()
    best_f = float("inf")
    calls = 0
    checkpoint = 0.
    nominal_scale = .020 ** 2

    class TimeLimit(Exception):
        pass

    def f_g(flat):
        nonlocal calls, best, best_f, checkpoint
        if time.monotonic() - start > a.seconds:
            raise TimeLimit
        yy = flat.reshape(r, b, c)
        delta = yy @ yy.transpose(0, 2, 1) - p0
        kd = np.zeros_like(gradients)
        for i in range(r):
            for j in range(r):
                g = cross[i, j]
                kd[i] += g @ delta[j] @ g.T
        err2sq = (model.e20 + 2 * np.einsum("rij,rij->", gradients, delta)
                  + np.einsum("rij,rij->", kd, delta))
        gradient = 4 * (gradients + kd) @ yy
        calls += 1
        if err2sq < best_f:
            best_f = float(err2sq)
            best = flat.copy()
        elapsed = time.monotonic() - start
        if elapsed >= checkpoint:
            print(json.dumps(dict(elapsed=elapsed, calls=calls, best_error_2=float(np.sqrt(best_f)))),
                  flush=True)
            checkpoint += 5
        return err2sq / nominal_scale, gradient.ravel() / nominal_scale

    initial, g = f_g(latest)
    rng = np.random.default_rng(20261115)
    direction = rng.normal(size=latest.size)
    direction /= np.linalg.norm(direction)
    eps = 1e-6
    fd = (f_g(latest + eps*direction)[0] - f_g(latest - eps*direction)[0]) / (2*eps)
    assert abs(fd - g @ direction) < 1e-5 * max(1., abs(fd))
    try:
        opt = minimize(f_g, latest, jac=True, method="L-BFGS-B",
                       options=dict(maxiter=3000, maxls=30, maxcor=30, ftol=1e-15, gtol=1e-10))
        end = str(opt.message)
    except TimeLimit:
        end = "wall-time limits reached"
    y = best.reshape(r, b, c)
    w = np.array([solve_triangular(ls[i].T, y[i], lower=False) for i in range(r)])
    # For the new W, fit d against exactly the old physical Hprime before
    # reporting H1. This leaves the two-body metrics and y unchanged.
    target = np.einsum("rbc,rc,rbd->d", orig_w, orig_d,
                        model.V.reshape(r, b, -1), optimize=True)
    design = np.einsum("rbc,rbd->rcd", w, model.V.reshape(r, b, -1),
                        optimize=True).reshape(r*c, -1).T
    correction = np.linalg.lstsq(design, target - design @ initial_d.ravel(), rcond=1e-12)[0]
    d = initial_d + correction.reshape(r, c)
    metrics = evaluate_dfthc_angle_words(words, w, d, model.S, model.beta, model.ref,
                                        brot=8, tree_edges=base["tree_edges"], energy_upper=UPPER_ENERGY)
    assert abs(metrics["error_2"] - np.sqrt(best_f)) < 1e-9
    data = dict(base)
    data["W"] = w
    data["H2_I"] = d + w.sum(axis=1)
    np.savez_compressed(a.output.with_suffix(".npz"), **data)
    result = dict(status="H2_ONLY_PSD_RANK_REDUCED_REFIT", rank=c, before_rank=prev_c,
                  source_npz_sha256=hashlib.sha256(a.npz.read_bytes()).hexdigest(),
                  actual_words_sha256=digest, error_2_start=float(np.sqrt(initial*nominal_scale)),
                  measured_error_2_gradient_direction=float(g@direction),
                  finite_difference=fd, termination=end, calls=calls,
                  seconds=time.monotonic()-start, official_numeric_metrics=metrics,
                  full_verifier_run=False)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
