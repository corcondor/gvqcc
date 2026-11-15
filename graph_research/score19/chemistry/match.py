"""Apply disjoint DF-THC column rotations selected by a weighted matching."""

import argparse
from itertools import combinations
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix

from inverse_v2_chemistry_gauge import norm, pair_minimum


def improving_edges(columns):
    edges = []
    for a, b in combinations(range(columns.shape[1]), 2):
        left, right = columns[:, a], columns[:, b]
        before = np.abs(left).sum() ** 2 + np.abs(right).sum() ** 2
        theta, after = pair_minimum(left, right)
        saving = float((before - after) / 4)
        if saving > 1e-12:
            edges.append((a, b, theta, saving))
    return edges


def select(edges, size):
    incidence = csc_matrix(
        (np.ones(2 * len(edges)), ([q for a, b, _, _ in edges for q in (a, b)],
                                  np.repeat(np.arange(len(edges)), 2))),
        shape=(size, len(edges)),
    )
    gains = np.array([edge[3] for edge in edges])
    result = milp(-gains / gains.max(), integrality=np.ones(len(edges)),
                  bounds=Bounds(0, 1), constraints=LinearConstraint(incidence, 0, 1))
    if not result.success:
        raise RuntimeError(result.message)
    return [edge for edge, choice in zip(edges, result.x) if choice > 0.5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sweeps", type=int, default=12)
    args = parser.parse_args()
    with ZipFile(args.archive) as portfolio, portfolio.open("dfthcsos/submission.npz") as member:
        data = dict(np.load(member, allow_pickle=False))
    original = np.concatenate((data["W"], data["H2_I"][:, None, :]), axis=1)
    state = original.copy()
    updates = []
    for step in range(args.sweeps):
        applied = []
        for group, columns in enumerate(state):
            edges = improving_edges(columns)
            if not edges:
                continue
            for a, b, theta, saving in select(edges, columns.shape[1]):
                left, right = columns[:, a].copy(), columns[:, b].copy()
                c, s = np.cos(theta), np.sin(theta)
                columns[:, a], columns[:, b] = c * left + s * right, c * right - s * left
                applied.append([group, a, b, theta, saving])
        if not applied:
            break
        updates.append({"sweep": step, "edges": applied, "lambda_h2": norm(state)})
    deviation = float(np.max(np.abs(original @ original.swapaxes(1, 2) - state @ state.swapaxes(1, 2))))
    report = {"lambda_h2_before": norm(original), "lambda_h2_after": norm(state),
              "max_gram_difference": deviation, "sweeps": updates}
    (args.output / "match.json").write_text(json.dumps(report, indent=2) + "\n")
    print({key: value for key, value in report.items() if key != "sweeps"}, flush=True)
    if updates:
        data["W"], data["H2_I"] = state[:, :-1, :], state[:, -1, :]
        np.savez_compressed(args.output / "submission.npz", **data)


if __name__ == "__main__":
    main()
