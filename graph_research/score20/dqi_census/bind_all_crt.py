"""Bind all scalar CRT synthesis forward calls in the pinned decoder."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from census import PIN, digest, intersection, open_columns, read_width, size, union
from split_crt import build


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("intervals", type=Path)
    cli.add_argument("report", type=Path)
    cli.add_argument("--dqi-source", type=Path, required=True)
    cli.add_argument("--prior-code", type=Path, required=True)
    args = cli.parse_args()
    assert digest(args.source) == PIN
    for folder in (args.prior_code, *(args.dqi_source / r for r in (
        "night_c27/synthesis", "night_c27/arithmetic", "after_c5/extractor_width",
    ))):
        sys.path.insert(0, str(folder))
    import dqi_ccx_peephole as binary
    import ew_paths  # noqa: F401
    import fused_crt_synthesis as synthesis
    import kickmix as km
    import kmb_profile
    from outcome_dqi_chart_match import match

    def open_path(path):
        return open_columns(path, binary.BinaryCircuit, kmb_profile)

    base = open_path(args.source)
    search_range = (21555411, 26452636)
    stage_hits = []
    with TemporaryDirectory() as folder:
        path = Path(folder) / "reference_prefix.kmb"
        next_start = search_range[0]
        for r in range(1, 35):
            node = 34 - r
            circuit, _, _, helpers = build(km, synthesis, r, node, False, False)
            assert helpers == 24
            circuit.to_file(path, format="kmb")
            template = open_path(path)
            source = list(template.operations(0, len(template.opcodes)))
            hits = []
            match_start = next_start
            while (idx := base.opcodes.find(template.opcodes, match_start, search_range[1])) >= 0:
                stop = idx + len(template.opcodes)
                if match(source, base.operations(idx, stop)) is not None:
                    hits.append((idx, stop))
                match_start = idx + 1
            assert len(hits) == 1, (r, hits)
            start, stop = hits[0]
            next_start = stop
            stage_hits.append(dict(r=r, node=node, start=start, end=stop,
                                   original_static_t=(r + 2) * 42))
            template.close()
            path.unlink()
    scopes = union([(row["start"], row["end"]) for row in stage_hits])
    widths = read_width(args.intervals, len(base.opcodes))
    covered = {}
    for threshold in (889, 881):
        hot = union([(a, b) for a, b, width in widths if width >= threshold])
        covered[threshold] = dict(whole=size(hot), within=size(intersection(hot, scopes)))
    report = dict(source_sha256=PIN, exact_synthesis_prefix_sites=len(stage_hits),
                  search_range=search_range, within=covered,
                  conditional_split_added_T_estimate=15 * len(stage_hits), matches=stage_hits)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print({k: v for k, v in report.items() if k != "matches"}, flush=True)
    base.close()


if __name__ == "__main__":
    main()
