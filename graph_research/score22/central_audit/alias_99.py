"""Test the installed rank-99 tensor's direct destination-alias obligations."""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import sys


def reachable(first, graph):
    undone = [first]
    seen = {first}
    while undone:
        i = undone.pop()
        for j in graph[i]:
            if j not in seen:
                undone.append(j)
                seen.add(j)
    return seen


def components(graph):
    reverse = [[] for _ in graph]
    for i, row in enumerate(graph):
        for j in row:
            reverse[j].append(i)
    undone = set(range(len(graph)))
    output = []
    while undone:
        i = min(undone)
        same = reachable(i, graph) & reachable(i, reverse)
        output.append(sorted(same))
        undone.difference_update(same)
    return output


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            leading = row.bit_length()
            if leading not in pivots:
                pivots[leading] = row
                break
            row ^= pivots[leading]
    return len(pivots)


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--report", type=Path, required=True)
    args = cli.parse_args()
    for rel in ("night_c27/synthesis", "night_c27/arithmetic", "after_c5/extractor_width"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import gf24_arithmetic as arithmetic
    import fused_crt_synthesis as synthesis
    from split_crt import forward_n_rows

    terms = arithmetic.tensor24()
    assert len(terms) == 99
    edges = [[] for _ in terms]
    diagonals = []
    for i, (_, right, direction) in enumerate(terms):
        if (right & direction).bit_count() & 1:
            diagonals.append(i)
        for j, (_, _, update) in enumerate(terms):
            if i != j and ((right & update).bit_count() & 1):
                edges[i].append(j)
    scc = sorted(map(len, components(edges)), reverse=True)
    scalar_map = forward_n_rows(synthesis, 34, 0)
    assert rank(scalar_map) == 34 * 12
    assert arithmetic.mul24(1, 1) == 1
    result = dict(
        product_terms=len(terms),
        disjoint_input_output_T=99,
        same_register_noninvertible_individual_updates=len(diagonals),
        index_of_noninvertible_updates=diagonals,
        pairwise_control_use_before_overwrite_edges=sum(map(len, edges)),
        strongly_connected_component_sizes=scc,
        scalar_map_binary_rank=rank(scalar_map),
        scalar_map_binary_columns=len(scalar_map),
        unit_counterexample=dict(D=1, P=1, required_multiplication=1, aliased_xor_accumulator=0),
        scope="Installed tensor factors with unchanged parity controls. No lower bound asserted "
              "for a different in-place factorization or restricted actual decoder states.",
    )
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print({k: v for k, v in result.items() if k != "index_of_noninvertible_updates"})


if __name__ == "__main__":
    main()
