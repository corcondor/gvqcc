#!/usr/bin/env python3
"""Experimental coupled ANGLE word / FeMoCo search (numerical, NOT native).

A bit flip of word (address, column) alters two adjacent XOR-transition
loaders: delta_k = word_k XOR word_(k-1). Screen its exact GF(2)
low/high mixed-ANF rank at BOTH boundaries, then test the mutated 7-bit
angle table against the FeMoCo numerical accuracy gates. An optional
regularized W/H2_I response reprojects the changed rank's channels.
A two-word beam uses *recomputed* ranks, never additive estimates.

Deliberately NOT a quantum-circuit compiler: mixed rank is not Toffolis.
No KMB is emitted. The source physics and FeMoCo reference data are
external pinned inputs, not redistributed by this repo.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np

N = 76
J = 5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as archive:
        return {k: archive[k].copy() for k in archive.files}


def gf2_rank(matrix: np.ndarray) -> int:
    """Exact GF(2) elimination, never numerical SVD rank."""
    arr = np.asarray(matrix, dtype=np.uint8)
    if arr.ndim != 2:
        raise ValueError("expected 2D bit matrix")
    pivots: dict[int, int] = {}
    for row in arr:
        x = int.from_bytes(np.packbits(row, bitorder="little").tobytes(), "little")
        while x:
            p = x.bit_length() - 1
            if p in pivots:
                x ^= pivots[p]
            else:
                pivots[p] = x
                break
    return len(pivots)


def batch_delta(words: np.ndarray, k: int, j: int = J) -> np.ndarray:
    if words.shape[1] % j:
        raise ValueError("angle columns must be divisible by J")
    if not 0 <= k < words.shape[1] // j:
        raise IndexError(k)
    out = np.array(words[:, k * j:(k + 1) * j], dtype=np.int64, copy=True)
    if k:
        out ^= words[:, (k - 1) * j:k * j]
    return out


def bit0_mixed_rank(words: np.ndarray, k: int, j: int = J) -> int:
    """Rank of (word x nonconstant low-ANF monomial) by high address.

    Uses complete 16-row address blocks only; a partial last block is
    excluded from this algebraic SCREEN, but included in physics checks.
    This rank is NOT a Toffoli count, an attainable lower bound, or an
    adequate surrogate for full multi-output XAG synthesis.
    """
    h = words.shape[0] // 16
    if h < 1:
        raise ValueError("no complete 16-row block")
    d = batch_delta(words, k, j)
    planes = (d[:h * 16] & 1).reshape(h, 16, j).transpose(2, 1, 0).copy()
    for bit in range(4):
        for low in range(16):
            if low & (1 << bit):
                planes[:, low, :] ^= planes[:, low ^ (1 << bit), :]
    return gf2_rank(planes[:, 1:, :].reshape(15 * j, h))


def rank_profile(words: np.ndarray) -> list[int]:
    return [bit0_mixed_rank(words, k) for k in range(words.shape[1] // J)]


@dataclass(frozen=True)
class Move:
    row: int
    column: int
    delta_rank: int
    weight_norm: float


def flip(words: np.ndarray, row: int, column: int) -> None:
    # Bit zero toggling preserves the preexisting signed-gauge high bits.
    words[row, column] ^= 1


def affected_slots(column: int, columns: int) -> tuple[int, ...]:
    k = column // J
    return (k, k + 1) if k + 1 < columns // J else (k,)


def rank_effect(words: np.ndarray, row: int, column: int, profile: list[int]) -> int:
    touched = affected_slots(column, words.shape[1])
    flip(words, row, column)
    try:
        after = sum(bit0_mixed_rank(words, k) for k in touched)
    finally:
        flip(words, row, column)
    return int(after - sum(profile[k] for k in touched))


def screen_moves(z: dict, top_rows: int, per_slot: int, profile: list[int]):
    W = z["W"]
    R, B, _ = W.shape
    words = z["angle_words"]
    if words.shape != (N + R * B, 75):
        raise ValueError("expected 75 Givens columns and N+R*B rows")
    norms = np.linalg.norm(W, axis=2)
    selected_rows = sorted((N + r * B + int(b), float(norms[r, b]))
                           for r in range(R) for b in np.argsort(norms[r])[:top_rows])
    moves = []
    summary = dict(tried=0, rank_improving=0, rank_tie=0, rank_worse=0)
    for row, weight in selected_rows:
        for col in range(words.shape[1]):
            dr = rank_effect(words, row, col, profile)
            summary["tried"] += 1
            if dr < 0:
                summary["rank_improving"] += 1
                moves.append(Move(row, col, dr, weight))
            elif dr == 0:
                summary["rank_tie"] += 1
            else:
                summary["rank_worse"] += 1
    moves.sort(key=lambda m: (m.delta_rank, m.weight_norm, m.row, m.column))
    kept, usage = [], {}
    for move in moves:
        slot = move.column // J
        if usage.get(slot, 0) < per_slot:
            kept.append(move)
            usage[slot] = usage.get(slot, 0) + 1
    return kept, {**summary, "selected": len(kept)}


def local_w_ridge_refit(z0: dict, z: dict, row: int, physical, module, ridge=1e-4):
    """Local packed-channel projection, NOT a full nonlinear constrained refit.

    Solve for W_new:
       ||P_new.T W_new - P_old.T W_old||_F^2
         + ridge ||W_new - W_old||_F^2 .
    Update H2_I so H2_I - sum_b W is invariant for this rank.
    Physics accuracy still MUST be checked after this approximate repair.
    """
    R, B, _ = z0["W"].shape
    r, b = divmod(row - N, B)
    if not 0 <= r < R:
        raise ValueError("only inner words may be refitted")
    old = module.decode(z0["angle_words"], z0["tree_edges"], beta=7)
    changed = module.decode(z["angle_words"], z["tree_edges"], beta=7)
    ii, jj, sc = physical.ii, physical.jj, physical.sc
    region = old[N + r * B:N + (r + 1) * B]
    P0 = region[:, ii] * region[:, jj] * sc
    P1 = P0.copy()
    v = changed[row]
    P1[b] = v[ii] * v[jj] * sc
    W0 = z0["W"][r]
    target = P0.T @ W0
    W1 = np.linalg.solve(P1 @ P1.T + ridge * np.eye(B),
                         P1 @ target + ridge * W0)
    z["W"][r] = W1
    z["H2_I"][r] = z0["H2_I"][r] + (W1 - W0).sum(axis=0)
    return float(np.linalg.norm(W1 - W0))


def physical_pass(m: dict) -> bool:
    return (m["error_1"] <= 0.02 and m["error_2"] <= 0.02
            and m["Lambda"] > 49 and m["E_gap"] > 3.914898
            and bool(m["gap_in_domain"]) and bool(np.isfinite(m["lambda_eff"])))


def load_physics(module_path: Path, data_path: Path):
    spec = importlib.util.spec_from_file_location("gvqcc_external_physical", module_path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load supplied physical module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Physical(data_path), module


def experiment(args):
    args.out.mkdir(parents=True, exist_ok=True)
    phys, module = load_physics(args.physical_module, args.reference)
    reports = []
    for fp in args.seeds:
        base = load(fp)
        if int(base.get("brot", 7)) != 7:
            raise ValueError("only 7-bit signed angle words in this experiment")
        baseline = phys.evaluate(base)
        if not physical_pass(baseline):
            raise ValueError(f"base fails numerical physical gates: {fp}")
        profile = rank_profile(base["angle_words"])
        moves, stats = screen_moves(base, args.top_rows, args.per_slot, profile)
        records, feasible = [], []
        best = None
        for move in moves:
            candidate = {k: v.copy() for k, v in base.items()}
            flip(candidate["angle_words"], move.row, move.column)
            for kind in (("raw", "ridge") if args.ridge else ("raw",)):
                z = {k: v.copy() for k, v in candidate.items()}
                changed_W_norm = 0.0
                if kind == "ridge":
                    changed_W_norm = local_w_ridge_refit(
                        base, z, move.row, phys, module, args.ridge_penalty)
                m = phys.evaluate(z)
                rec = dict(moves=[asdict(move)], kind=kind,
                           rank_delta=move.delta_rank, valid=physical_pass(m),
                           W_update_norm=changed_W_norm,
                           error_1=float(m["error_1"]), error_2=float(m["error_2"]),
                           Lambda=float(m["Lambda"]), E_gap=float(m["E_gap"]),
                           lambda_eff=float(m["lambda_eff"]))
                records.append(rec)
                if rec["valid"]:
                    feasible.append((rec, z))
                    if best is None or (rec["rank_delta"], rec["lambda_eff"]) < (
                            best[0]["rank_delta"], best[0]["lambda_eff"]):
                        best = rec, z

        # Second step: non-adjacent slots, two full word edits, recomputed rank.
        # A parent with local W-refit may be used; second word is not refitted.
        two_hop_checks = 0
        if args.beam_width:
            beam = sorted(feasible, key=lambda pair: (
                pair[0]["rank_delta"], pair[0]["lambda_eff"], pair[0]["moves"][0]["row"]
            ))[:args.beam_width]
            for parent, z1 in beam:
                first = parent["moves"][0]
                prof1 = rank_profile(z1["angle_words"])
                for other in moves:
                    if other.row == first["row"] and other.column == first["column"]:
                        continue
                    if abs(other.column // J - first["column"] // J) < 2:
                        continue
                    dr = rank_effect(z1["angle_words"], other.row, other.column, prof1)
                    if dr >= 0:
                        continue
                    z2 = {k: v.copy() for k, v in z1.items()}
                    flip(z2["angle_words"], other.row, other.column)
                    m = phys.evaluate(z2)
                    total = sum(rank_profile(z2["angle_words"])) - sum(profile)
                    rec = dict(moves=[first, asdict(other)], kind="two_word_after_" + parent["kind"],
                               rank_delta=int(total), valid=physical_pass(m),
                               error_1=float(m["error_1"]), error_2=float(m["error_2"]),
                               Lambda=float(m["Lambda"]), E_gap=float(m["E_gap"]),
                               lambda_eff=float(m["lambda_eff"]))
                    records.append(rec)
                    two_hop_checks += 1
                    if rec["valid"] and (best is None or
                        (rec["rank_delta"], rec["lambda_eff"]) <
                        (best[0]["rank_delta"], best[0]["lambda_eff"])):
                        best = rec, z2

        output_name = fp.stem + "_coupled_numeric_only.npz"
        if best:
            chosen, z = best
            R, B, _ = z["W"].shape
            decoded = module.decode(z["angle_words"], z["tree_edges"], beta=7)
            z["U"] = decoded[N:].reshape(R, B, N)
            np.savez_compressed(args.out / output_name, **z)

        report = dict(
            seed=str(fp), seed_sha256=sha256(fp),
            reference_sha256=sha256(args.reference),
            base_physics=baseline, base_mixed_bit0_rank=profile,
            base_rank_sum=int(sum(profile)), screen=stats,
            two_hop_exact_checks=two_hop_checks,
            evaluated_variant_count=len(records),
            valid_variant_count=sum(bool(r["valid"]) for r in records),
            best=best[0] if best else None,
            best_numeric_npz=output_name if best else None,
            all_evaluated=records, full_KMB_generated=False,
            official_KickMix_verified=False,
            score_status="NO_SCORE_MEASURED_RANK_PROXY_NOT_TOFFOLIS"
        )
        (args.out / (fp.stem + "_receipt.json")).write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        reports.append(report)
        print(json.dumps(dict(seed=fp.name, profile_sum=sum(profile), **stats,
                              checked=len(records), valid=report["valid_variant_count"],
                              best=report["best"]), ensure_ascii=False), flush=True)
    return reports


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=Path, nargs="+", required=True)
    p.add_argument("--physical-module", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--top-rows", type=int, default=5)
    p.add_argument("--per-slot", type=int, default=2)
    p.add_argument("--ridge", action="store_true")
    p.add_argument("--ridge-penalty", type=float, default=1e-4)
    p.add_argument("--beam-width", type=int, default=0)
    args = p.parse_args()
    if args.top_rows < 1 or args.per_slot < 1 or args.beam_width < 0 or args.ridge_penalty <= 0:
        p.error("top-rows, per-slot, ridge-penalty must be positive; beam-width nonnegative")
    experiment(args)


if __name__ == "__main__":
    main()
