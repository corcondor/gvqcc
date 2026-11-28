#!/usr/bin/env python3
"""C=43/42 official 8-bit angle words, CPU/CUDA numerical search.

The source NPZ is an already verified C44 family. This script changes only W
and H2_I, not the 15 ANGLE loaders or the quantized word table.
It does not submit to Kaggle. All finalists are rechecked by the unchanged
official numerical evaluator; optional full ANGLE verification is explicit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def resource_cost(rank, r, b, n, j, loader_t, loader_temp):
    from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1
    p = SpinFreeData_V1(R=r, B=b, C=rank, N=n, chi=10, beta=8)
    t = p.outer_state_prep() + p.inner_state_prep() + p.givens_rotations() + 2 * loader_t
    qo, qi = p.outer_state_prep_qubit_cost(), p.inner_state_prep_qubit_cost()
    q = qo["persistent"] + qi["persistent"] + 8 * j + max(
        qo["temporary"], qi["temporary"], loader_temp
    )
    return int(t), int(q)


def compressed_start(base, gram, rank, seed, jitter=0.0):
    """Projector-Gram low-rank initializer with native d=H2_I-sum(W)."""
    w0, i0 = base["W"], base["H2_I"]
    r, b, c0 = w0.shape
    assert 1 <= rank <= c0 and i0.shape == (r, c0)
    rng = np.random.default_rng(seed)
    w = np.empty((r, b, rank))
    d = np.empty((r, rank))
    native = i0 - w0.sum(axis=1)
    for g in range(r):
        wc = w0[g].copy()
        if jitter:
            wc += jitter * np.linalg.norm(wc) / np.sqrt(wc.size) * rng.normal(size=wc.shape)
        eig, vec = np.linalg.eigh(wc.T @ gram[g, g] @ wc)
        u = vec[:, np.argsort(eig)[-rank:]]
        w[g], d[g] = wc @ u, native[g] @ u
    return w, d


def as_candidate(base, w, d):
    return {**base, "W": w, "H2_I": d + w.sum(axis=1)}


def passes(m):
    return (
        m["error_1"] <= .020 and m["error_2"] <= .020 and
        m["Lambda"] > 49 and m["E_gap"] > 3.914898 and
        0 < m["E_gap"] < 2 * m["Lambda"] and
        math.isfinite(m["lambda_eff"])
    )


class GpuModel:
    """Float64 surrogate using *actual* fixed-angle word projector tensors."""
    def __init__(self, model, device):
        import torch
        self.torch, self.device = torch, torch.device(device)
        def t(x):
            return torch.as_tensor(np.array(x, copy=True), device=device, dtype=torch.float64)
        self.r, self.b, _ = model.base["W"].shape
        self.n = model.N
        self.g4, self.a, self.p0 = t(model.G4), t(model.A), t(model.P0)
        self.e20 = t(model.e20)
        self.outer = t(model.outer.reshape(self.r, self.b, self.n, self.n))
        self.hbase, self.one, self.gap_const = t(model.hbase), t(model.one), t(model.gap_const)

    def metrics(self, w, d):
        torch = self.torch
        ii = d + w.sum(dim=1)
        delta = w @ w.transpose(1, 2) - self.p0
        kd = torch.zeros_like(delta)
        for s in range(self.r):
            gs = self.g4[:, s]
            kd = kd + gs @ delta[s] @ gs.transpose(1, 2)
        e2sq = self.e20 + 2 * (self.a * delta).sum() + (kd * delta).sum()
        x = torch.einsum("rbc,rbpq->rcpq", w, self.outer)
        h = self.hbase - torch.einsum("rc,rcpq->pq", d, x)
        eig, vec = torch.linalg.eigh(h)
        from scipy.optimize import linear_sum_assignment
        rows, cols = linear_sum_assignment(-np.abs((self.one @ vec).detach().cpu().numpy()))
        match = np.empty(self.n, dtype=int)
        match[rows] = cols
        qrec = torch.einsum(
            "j,jp,jq->pq",
            eig[torch.as_tensor(match, device=self.device)], self.one, self.one
        )
        error1 = torch.linalg.matrix_norm(qrec - h)
        error2 = torch.sqrt(torch.clamp(e2sq, min=1e-30))
        l1 = torch.abs(w).sum(dim=1) + torch.abs(ii)
        lam1 = torch.abs(eig).sum()
        lam = lam1 + .25 * (l1 * l1).sum()
        gap = self.gap_const + lam1 - eig.sum() + .5 * (d * d).sum()
        eff = torch.sqrt(torch.clamp(gap * (2 * lam - gap), min=1e-30))
        return {"error_1": error1, "error_2": error2,
                "Lambda": lam, "E_gap": gap, "lambda_eff": eff}

    def objective(self, w, d, penalty):
        torch = self.torch
        m = self.metrics(w, d)
        violation = sum(
            torch.relu(m[k] / .0199 - 1)**2 for k in ("error_1", "error_2")
        )
        violation += torch.relu((3.914899 - m["E_gap"]) / .01)**2
        violation += torch.relu((49.00001 - m["Lambda"]) / 10)**2
        return torch.log(m["lambda_eff"]) + penalty * violation


def run(args):
    import torch
    from inverse_v2_chemistry_refit import FixedAngles
    from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
    from dfthcsos.scoreinfra.reference import UPPER_ENERGY

    base_path = Path(args.base_npz)
    base = dict(np.load(base_path, allow_pickle=False))
    fixed = FixedAngles(base)
    r, b, c = base["W"].shape
    if (r, b, c) != (8, 143, 44):
        raise ValueError(f"Expected 8x143x44, got {(r, b, c)}")
    t44, q44 = resource_cost(44, r, b, fixed.N, args.j, args.loader_t, args.loader_temp)
    if t44 != args.assert_t44 or q44 != args.assert_q44:
        raise ValueError(f"Public loader mismatch: T={t44}, Q={q44}")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    model = GpuModel(fixed, args.device)
    rows = []

    for rank in args.ranks:
        t, q = resource_cost(rank, r, b, fixed.N, args.j, args.loader_t, args.loader_temp)
        for trial in range(args.seeds):
            w0, d0 = compressed_start(
                base, fixed.G4, rank, 20261116 + 100 * rank + trial,
                jitter=0.0 if trial == 0 else min(.015, .003 * trial)
            )
            if args.warmstart_dir:
                checkpoint = Path(args.warmstart_dir) / f"C{rank}_seed{trial}.npz"
                if checkpoint.exists():
                    init = dict(np.load(checkpoint, allow_pickle=False))
                    if init["W"].shape != (r, b, rank) or init["H2_I"].shape != (r, rank):
                        raise ValueError(f"Warmstart shape mismatch: {checkpoint}")
                    w0 = init["W"]
                    d0 = init["H2_I"] - w0.sum(axis=1)
            w = torch.nn.Parameter(torch.as_tensor(w0.copy(), device=args.device, dtype=torch.float64))
            d = torch.nn.Parameter(torch.as_tensor(d0.copy(), device=args.device, dtype=torch.float64))
            optimizer = torch.optim.Adam([w, d], lr=args.lr)
            best = None
            def record(step):
                nonlocal best
                with torch.no_grad():
                    m = {k: float(v) for k, v in model.metrics(w, d).items()}
                excess = sum(max(0.0, m[k] / .020 - 1) for k in ("error_1", "error_2"))
                excess += max(0., (3.914898 - m["E_gap"]) / .01)
                excess += max(0., (49.0 - m["Lambda"]) / 10)
                key = (excess > 0, excess, m["lambda_eff"] * t * q)
                if best is None or key < best[0]:
                    best = (key, w.detach().cpu().numpy().copy(),
                            d.detach().cpu().numpy().copy(), step)
            record(0)
            for step in range(1, args.steps + 1):
                penalty = [1., 10., 100., 1000., 10000.][min(4, (step - 1) * 5 // args.steps)]
                optimizer.zero_grad(set_to_none=True)
                loss = model.objective(w, d, penalty)
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"Nonfinite objective C={rank}, seed={trial}, step={step}")
                loss.backward()
                torch.nn.utils.clip_grad_norm_([w, d], 10.)
                optimizer.step()
                if step % args.check_each == 0 or step == args.steps:
                    record(step)
            _, wbest, dbest, best_step = best
            cand = as_candidate(base, wbest, dbest)
            exact = evaluate_dfthc_angle_words(
                cand["angle_words"], cand["W"], cand["H2_I"] - cand["W"].sum(1),
                fixed.S, fixed.beta, fixed.ref, brot=8,
                tree_edges=cand["tree_edges"], energy_upper=UPPER_ENERGY
            )
            chemistry_cost = float(exact["lambda_eff"] * t * q)
            eligible = passes(exact) and chemistry_cost < args.max_chemistry_cost
            stem = f"C{rank}_seed{trial}"
            path = out / f"{stem}.npz"
            np.savez_compressed(path, **cand)
            report = {
                "rank": rank, "trial": trial, "step": best_step,
                "T_model": t, "Q_model": q, "cost_model": chemistry_cost,
                "official_numeric_metrics": exact,
                "source_sha256": digest(base_path), "candidate_sha256": digest(path),
                "numeric_eligible": eligible, "full_native_verified": False,
                "status": "NUMERIC_ONLY" if eligible else "REJECT"
            }
            if eligible and args.angle_dir:
                from dfthcsos.verify import verify
                full = verify(Path(args.angle_dir), path, tree_edges=cand["tree_edges"])
                report["official_native_receipt"] = full
                ok = (full.get("status") == "PASS" and
                      int(full.get("verified_shots", 0)) >= 78080 and
                      int(full.get("toffoli_count", -1)) == t and
                      int(full.get("num_qubits", -1)) == q and
                      float(full.get("score", float("inf"))) < args.max_chemistry_cost)
                report["full_native_verified"] = ok
                report["status"] = "OFFICIAL_PASS" if ok else "REJECT_RESOURCE_OR_COST"
            (out / f"{stem}.json").write_text(
                json.dumps(report, indent=2, allow_nan=False) + "\n"
            )
            rows.append({k: report[k] for k in
                ("rank", "trial", "cost_model", "numeric_eligible", "full_native_verified", "status")})
            print(json.dumps(rows[-1]), flush=True)
    (out / "summary.json").write_text(
        json.dumps({"rows": rows, "source": digest(base_path),
                    "device": args.device, "verified_submission": False}, indent=2) + "\n"
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-npz", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--angle-dir")
    p.add_argument("--warmstart-dir")
    p.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    p.add_argument("--ranks", type=int, nargs="+", choices=(43, 42), default=[43, 42])
    p.add_argument("--steps", type=int, default=1200)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--check-each", type=int, default=25)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--loader-t", type=int, default=4025)
    p.add_argument("--loader-temp", type=int, default=77)
    p.add_argument("--j", type=int, default=5)
    p.add_argument("--assert-t44", type=int, default=14712)
    p.add_argument("--assert-q44", type=int, default=427)
    p.add_argument("--max-chemistry-cost", type=float, default=294762732.98)
    args = p.parse_args()
    if min(args.steps, args.seeds, args.check_each, args.loader_t) <= 0:
        p.error("positive count parameters required")
    if not (math.isfinite(args.lr) and args.lr > 0):
        p.error("positive finite learning rate required")
    import torch
    if args.device == "cuda" and not torch.cuda.is_available():
        p.error("CUDA not available; choose --device cpu")
    run(args)


if __name__ == "__main__":
    main()
