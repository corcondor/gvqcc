"""Exact two-column orthogonal gauge search for DFTHCSOS weights.

An orthogonal transformation of ensemble columns acts on both W (lowercase
weights) and H2_I. It preserves the represented H2 tensor and the H1
contraction, as well as the identity-offset norm. Thus errors and E_gap do
not change, while lambda_h2 can change. No reference Hamiltonian is needed
to prove these invariants. Actual official verification remains a separate
acceptance gate.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np


def pair_minimum(a, b):
    """Global minimum of squared L1 norms of a rotated pair, 0<=theta<=pi/2."""
    sa = np.where(a != 0, np.sign(a), np.sign(b))
    sb = np.where(b != 0, np.sign(b), -np.sign(a))
    ac, ass = sa @ a, sa @ b
    bc, bs = sb @ b, -(sb @ a)
    diff = a * b < 0
    same = a * b > 0
    ia, ib = np.flatnonzero(diff), np.flatnonzero(same)
    angles = np.r_[np.arctan(-a[ia] / b[ia]), np.arctan(b[ib] / a[ib])]
    changes = np.zeros((len(angles), 4))
    changes[: len(ia), 0] = -2 * sa[ia] * a[ia]
    changes[: len(ia), 1] = -2 * sa[ia] * b[ia]
    changes[len(ia) :, 2] = -2 * sb[ib] * b[ib]
    changes[len(ia) :, 3] = 2 * sb[ib] * a[ib]
    order = np.argsort(angles)
    angles, changes = angles[order], changes[order]
    coeff = np.r_[np.zeros((1, 4)), np.cumsum(changes, axis=0)]
    coeff += np.array([ac, ass, bc, bs])
    lower = np.r_[0.0, angles]
    upper = np.r_[angles, np.pi / 2]
    ac, ass, bc, bs = coeff.T
    k0 = .5 * (ac * ac + ass * ass + bc * bc + bs * bs)
    kc = .5 * (ac * ac - ass * ass + bc * bc - bs * bs)
    ks = ac * ass + bc * bs
    candidate = .5 * np.mod(np.arctan2(ks, kc) + np.pi, 2 * np.pi)
    interior = (candidate >= lower) & (candidate <= upper)
    f = k0 + kc * np.cos(2 * lower) + ks * np.sin(2 * lower)
    theta = lower.copy()
    fi = k0 - np.hypot(kc, ks)
    use = interior & (fi < f)
    f[use], theta[use] = fi[use], candidate[use]
    i = int(np.argmin(f))
    theta = float(theta[i])
    c, s = np.cos(theta), np.sin(theta)
    aa, bb = c * a + s * b, -s * a + c * b
    actual = float(np.abs(aa).sum() ** 2 + np.abs(bb).sum() ** 2)
    original = float(np.abs(a).sum() ** 2 + np.abs(b).sum() ** 2)
    if actual >= original:
        return 0.0, original
    return theta, actual


def norm(z):
    return float(.25 * np.square(np.abs(z).sum(axis=1)).sum())


def search(z, max_seconds, max_sweeps):
    result = z.copy()
    transforms = np.broadcast_to(np.eye(z.shape[2]), (z.shape[0], z.shape[2], z.shape[2])).copy()
    start = time.monotonic()
    trace = []
    for sweep in range(max_sweeps):
        changed = 0
        old = norm(result)
        largest = 0.0
        for r in range(z.shape[0]):
            for j in range(z.shape[2]):
                for k in range(j + 1, z.shape[2]):
                    a, b = result[r, :, j], result[r, :, k]
                    original = float(np.abs(a).sum() ** 2 + np.abs(b).sum() ** 2)
                    theta, minimum = pair_minimum(a, b)
                    improvement = original - minimum
                    if improvement > max(1e-13, original * 2e-14):
                        c, s = np.cos(theta), np.sin(theta)
                        aa, bb = a.copy(), b.copy()
                        result[r, :, j], result[r, :, k] = c * aa + s * bb, -s * aa + c * bb
                        aa, bb = transforms[r, :, j].copy(), transforms[r, :, k].copy()
                        transforms[r, :, j], transforms[r, :, k] = c * aa + s * bb, -s * aa + c * bb
                        changed += 1
                        largest = max(largest, improvement / 4)
                if time.monotonic() - start > max_seconds:
                    break
            if time.monotonic() - start > max_seconds:
                break
        item = {"sweep": sweep, "lambda_h2": norm(result), "improvement": old - norm(result), "changed_pairs": changed, "largest_improvement": largest, "seconds": time.monotonic() - start}
        trace.append(item)
        print(json.dumps(item), flush=True)
        if changed == 0 or time.monotonic() - start > max_seconds:
            break
    return result, transforms, trace


def main():
    p = argparse.ArgumentParser()
    p.add_argument("baseline", type=Path)
    p.add_argument("--refit", type=Path)
    p.add_argument("--seconds", type=float, default=45)
    p.add_argument("--sweeps", type=int, default=8)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    data = dict(np.load(args.baseline))
    if args.refit:
        data.update(dict(np.load(args.refit)))
    z = np.concatenate((data["W"], data["H2_I"][:, None, :]), axis=1)
    optimized, transforms, trace = search(z, args.seconds, args.sweeps)
    before, after = norm(z), norm(optimized)
    orth_error = float(np.max(np.abs(transforms @ transforms.transpose(0, 2, 1) - np.eye(z.shape[2]))))
    gram_error = float(np.max(np.abs(z @ z.transpose(0, 2, 1) - optimized @ optimized.transpose(0, 2, 1))))
    data["W"], data["H2_I"] = optimized[:, :-1, :], optimized[:, -1, :]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **data)
    report = {"source": str(args.baseline), "refit": str(args.refit), "lambda_h2_before": before, "lambda_h2_after": after, "absolute_improvement": before - after, "orthogonality_max_error": orth_error, "extended_gram_max_error": gram_error, "trace": trace, "official_verified": False}
    args.out.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
