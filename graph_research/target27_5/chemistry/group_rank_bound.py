#!/usr/bin/env python3
"""Bound rank in each fixed DF-THC group using dual projector spaces."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import block_diag, eigh, inv, solve_triangular
from scipy.sparse.linalg import LinearOperator, cg
from chem_next_fixed_angles import FastFixedAngles


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--npz", required=True, type=Path)
    p.add_argument("--words", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--save-projection", type=Path)
    a = p.parse_args()
    start = time.monotonic()
    d = dict(np.load(a.npz, allow_pickle=False))
    words = np.load(a.words, allow_pickle=False)[:1220].astype(np.uint8)
    digest = hashlib.sha256(words.tobytes()).hexdigest()
    assert digest == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    d["angle_words"] = words
    m = FastFixedAngles(d)
    r, b, c = d["W"].shape

    cholesky = np.array([np.linalg.cholesky(m.G4[i, i]) for i in range(r)])
    q = np.array([solve_triangular(cholesky[i], m.V[i*b:(i+1)*b], lower=True)
                  for i in range(r)])
    grp = q.reshape(r*b, -1)
    gram = grp @ grp.T
    gram_blocks = gram.reshape(r, b, r, b).transpose(0, 2, 1, 3)
    assert max(np.linalg.norm(gram_blocks[i, i] - np.eye(b)) for i in range(r)) < 1e-10
    # A stores feature-residual-feature contractions at the original solution.
    # Let the unknown fit be a symmetric block delta relative to that solution.
    rhs = []
    for i in range(r):
        left = solve_triangular(cholesky[i], m.A[i], lower=True)
        rhs.append(-solve_triangular(cholesky[i], left.T, lower=True).T)
    rhs = np.array(rhs)
    clicks = 0

    def normal(flat):
        nonlocal clicks
        clicks += 1
        delta = flat.reshape(r, b, b)
        acc = np.zeros_like(delta)
        for i in range(r):
            for j in range(r):
                g = gram_blocks[i, j]
                acc[i] += g @ delta[j] @ g.T
        return acc.ravel()

    op = LinearOperator((r*b*b, r*b*b), matvec=normal, dtype=np.float64)
    flat, status = cg(op, rhs.ravel(), rtol=1e-12, atol=1e-16, maxiter=1000)
    response = normal(flat)
    opt_error_sq = max(0., m.e20 - 2 * np.dot(rhs.ravel(), flat) + np.dot(flat, response))
    err_normal = float(np.linalg.norm(response-rhs.ravel()))
    min_eig = float(eigh(gram, eigvals_only=True, subset_by_index=[0, 0])[0])
    # Delta in represented Hamiltonian between numerical and exact minimizers.
    uncertainty = err_normal / min_eig
    outside_lower = max(0., opt_error_sq-uncertainty**2)
    y = cholesky.transpose(0, 2, 1) @ d["W"]
    fit = flat.reshape(r, b, b) + y @ y.transpose(0, 2, 1)
    inv_gram = inv(gram)
    inv_blocks = inv_gram.reshape(r, b, r, b).transpose(0, 2, 1, 3)
    inv_square_roots = []
    for i in range(r):
        values, vec = eigh(inv_blocks[i, i], check_finite=False)
        inv_square_roots.append((vec / np.sqrt(values)) @ vec.T)
    dual_gram = [[inv_square_roots[i] @ inv_blocks[i, j] @ inv_square_roots[j]
                  for j in range(r)] for i in range(r)]
    # If P_i are the projections onto dual group subspaces, use
    # ||sum_i [X -> P_i X P_i]|| <= lambda_max(D),
    # with D_ij = ||O_i^T O_j||_2^2. This is the block Gram comparison
    # on the direct sum of group matrix spaces.
    d_norm = np.array([[np.linalg.norm(dual_gram[i][j], ord=2)**2
                        for j in range(r)] for i in range(r)])
    amplification = np.linalg.eigvalsh(d_norm)[-1]
    eigs = [np.linalg.eigvalsh(inv_square_roots[i] @ fit[i] @ inv_square_roots[i])[::-1]
            for i in range(r)]
    large_cholesky = np.linalg.cholesky(gram)
    orthogonal_representation = large_cholesky.T @ block_diag(*fit) @ large_cholesky
    grouped_fit_spectrum = eigh(orthogonal_representation, eigvals_only=True, check_finite=False)[::-1]
    if a.save_projection:
        np.savez(a.save_projection, target=orthogonal_representation,
                 features=large_cholesky.T, gram=gram, outside_lower=outside_lower,
                 uncertainty=uncertainty, group_count=r, group_size=b)
    candidates = []
    for rank in range(35, 45):
        tails = []
        for values in eigs:
            omitted = values.copy()
            omitted[:rank] = np.minimum(omitted[:rank], 0)
            tails.append(float(np.linalg.norm(omitted)))
        represented_lower = max(0., np.linalg.norm(tails)/np.sqrt(amplification)-uncertainty)
        omitted_global = grouped_fit_spectrum.copy()
        omitted_global[:rank*r] = np.minimum(omitted_global[:rank*r], 0)
        global_rank_penalty = max(0., np.linalg.norm(omitted_global)-uncertainty)
        combined = np.sqrt(outside_lower+max(represented_lower,global_rank_penalty)**2)
        candidates.append(dict(C=rank, group_tails=tails, global_rank_penalty=global_rank_penalty,
                               dual_rank_penalty=represented_lower, lower_error2=combined,
                               exceeds_tolerance=bool(combined > .020)))
    report = dict(status="JOINT_FIXED_GROUP_AND_RANK_NECESSARY_BOUND", words_sha256=digest,
                  npz_sha256=hashlib.sha256(a.npz.read_bytes()).hexdigest(),
                  unstructured_within_groups_relaxation_error2=np.sqrt(opt_error_sq),
                  gram_min_eigenvalue=min_eig, normal_equation_residual=err_normal,
                  fit_representation_uncertainty_bound=uncertainty,
                  dual_projection_amplification_upper_bound=amplification,
                  solver_convergence_status=status, solver_matvec=clicks,
                  records=candidates, seconds=time.monotonic()-start,
                  scope="Float64 evaluation of a necessary bound at the same word partition. Not interval-certified.")
    a.out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
