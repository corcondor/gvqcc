"""Order bilinear terms to minimize simultaneous input/output basis ranks."""

from argparse import ArgumentParser
from itertools import product
import json
from pathlib import Path
from random import Random
import sys


def insert(vector, basis):
    while vector:
        pivot = vector.bit_length() - 1
        if not basis[pivot]:
            basis[pivot] = vector
            return True
        vector ^= basis[pivot]
    return False


def ranks(sequence, columns):
    basis = [0] * 24
    values = [0]
    for pos in sequence:
        values.append(values[-1] + int(insert(columns[pos], basis)))
    return values


def trace(sequence, right, output):
    pending = ranks(reversed(sequence), right)[::-1]
    seen = ranks(sequence, output)
    return [pending[i] + seen[i + 1] for i in range(len(sequence))]


def quality(trace):
    return max(trace), sum(x * x for x in trace)


def ordered_blocks(terms, groups):
    """Exact subset DP on supplied groups, with original within-group order."""
    n = len(groups)
    right = [b for _, b, _ in terms]
    output = [c for _, _, c in terms]
    group_membership = []
    for mask in range(1 << n):
        group_membership.append([i for j, g in enumerate(groups) if mask >> j & 1 for i in g])
    full = (1 << n) - 1
    states = [(1000, 0, ()) for mask in range(full + 1)]
    states[0] = (0, 0, ())
    for mask in range(1, full + 1):
        for j in range(n):
            if mask >> j & 1:
                prior = mask ^ (1 << j)
                c0 = group_membership[prior]
                r0 = group_membership[full ^ mask]
                g = groups[j]
                c = ranks(c0 + g, output)[len(c0):]
                r = ranks(r0 + g[::-1], right)[len(r0):][::-1]
                cost = [r[k] + c[k + 1] for k in range(len(g))]
                best, area, order = states[prior]
                states[mask] = min(states[mask], (max(best, max(cost)),
                                                 area + sum(x * x for x in cost),
                                                 order + (j,)))
    return [i for j in states[full][2] for i in groups[j]]


def monte_carlo(order, right, output, steps, seed):
    rng = Random(seed)
    winner, best = order[:], quality(trace(order, right, output))
    for _ in range(max(1, steps // 250)):
        sequence = winner[:]
        previous = best
        for _ in range(250):
            a, b = sorted(rng.sample(range(len(order)), 2))
            trial = sequence[:]
            if rng.random() < .5:
                trial[a], trial[b] = trial[b], trial[a]
            else:
                trial.insert(b, trial.pop(a))
            result = quality(trace(trial, right, output))
            if result < best:
                best, winner = result, trial[:]
            if result <= previous or rng.random() < .025:
                sequence, previous = trial, result
    return winner


def tensor12x3(field, kernel, delta):
    low = [(a, b, c | c << 12) for a, b, c in kernel(12)]
    cross = [(a | a << 12, b | b << 12, c << 12) for a, b, c in kernel(12)]
    high = [(a << 12, b << 12, field.mul(delta, c)) for a, b, c in kernel(12)]
    return low + cross + high, [list(range(i, i + len(low))) for i in (0, len(low), 2 * len(low))]


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--steps", type=int, default=10000)
    args = cli.parse_args()
    for rel in ("after_c5/extractor_width", "night_c27/arithmetic"):
        sys.path.insert(0, str(args.source / rel))
    import direct_carry_arithmetic as source
    from tower_inverse import kernel

    production = source.A.tensor24()
    alternate, groups = tensor12x3(source.A.FIELD, kernel, source.A.DEFAULT_DELTA)
    records = []
    for label, terms, blocks in (("production", production, [list(range(i, i + 9))
                                                              for i in range(0, 99, 9)]),
                                  ("quadratic12", alternate, groups)):
        for a, b in product(range(24), repeat=2):
            truth = 0
            for x, y, c in terms:
                if (x >> a & 1) and (y >> b & 1):
                    truth ^= c
            assert truth == source.A.mul24(1 << a, 1 << b)
        right = [b for _, b, _ in terms]
        output = [c for _, _, c in terms]
        direct = list(range(len(terms)))
        blocked = ordered_blocks(terms, blocks)
        best = monte_carlo(blocked, right, output, args.steps, 118174)
        records.append(dict(label=label, terms=len(terms), ordinary=quality(trace(direct, right, output)),
                            block_dp=quality(trace(blocked, right, output)),
                            searched=quality(trace(best, right, output)), order=best,
                            live_slots=trace(best, right, output),
                            tensor=[terms[i] for i in best]))
        print({k: v for k, v in records[-1].items() if k in ("label", "terms", "ordinary",
                                                           "block_dp", "searched")}, flush=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
