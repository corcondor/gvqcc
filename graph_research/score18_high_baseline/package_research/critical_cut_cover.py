"""Find ancilla lifetimes shared by every forced maximum-width DAG cut."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from html import escape
from itertools import groupby
import json
from pathlib import Path
import sys

repository_section = Path(__file__).resolve().parent.parent
shared_code = repository_section / "invsqrt_graph"
sys.path.insert(0, str(shared_code if shared_code.exists() else repository_section))
import width_dag as dag


def load_pinned(source):
    source_hash = sha256(source.read_bytes()).hexdigest()
    if source_hash != dag.PIN:
        raise ValueError(f"Expected the score18 invsqrt KMB, got {source_hash}")
    lines = [
        line for line in str(dag.km.Circuit.from_file(source)).splitlines()
        if line.split()[0] not in {"APPEND_TO_REGISTER", "REGISTER"}
    ]
    gates = [dag.Gate.parse(line) for line in lines]
    return source_hash, lines, gates


def scan(source):
    source_hash, lines, gates = load_pinned(source)
    lifetimes, width, _ = dag.packed_lifetimes(gates)
    atoms, intervals, origin = dag.collapse_scopes(gates, lifetimes)
    pred, succ = dag.dependency_dag(atoms)
    starts, ends = [0] * len(atoms), [0] * len(atoms)
    for i, (_, birth, death) in enumerate(intervals):
        starts[birth] |= 1 << i
        ends[death] |= 1 << i
    ancestor = dag.closures(pred, starts)
    descendant = dag.closures(succ, ends, reverse=True)
    need = width - dag.INPUTS
    masks = Counter()
    anchors = []
    for at, (before, after, stop) in enumerate(zip(ancestor, descendant, ends)):
        live = before & (after ^ stop)
        if live.bit_count() == need:
            masks[live] += 1
            # The cut follows the entire atom, including a collapsed scope.
            anchors.append(origin[at + 1] - 1 if at + 1 < len(origin) else len(gates) - 1)
    if not masks:
        raise ValueError("No forced cuts at the original peak width")
    common = next(iter(masks))
    for live in masks:
        common &= live
    shared = []
    for i, (wire, birth, death) in enumerate(intervals):
        if common & (1 << i):
            start = origin[birth]
            end = origin[death]
            shared.append(dict(wire=f"q{wire}", birth=start, death=end,
                               birth_gate=lines[start], death_gate=lines[end]))
    shared.sort(key=lambda entry: entry["wire"])
    return dict(
        source_sha256=source_hash,
        legal_inputs=dag.DOMAIN,
        operations=len(gates),
        scope_collapsed_vertices=len(atoms),
        scope_collapsed_lifetimes=len(intervals),
        forced_width=width,
        fixed_input_width=dag.INPUTS,
        forced_cuts=len(anchors),
        distinct_live_sets=len(masks),
        common_lifetimes=shared,
        first_forced_cut=anchors[0],
        last_forced_cut=anchors[-1],
        indices="Zero-based KMB gate indices with register declarations omitted. "
                "Each cut follows the listed gate, at the end of a collapsed scope.",
    ), anchors


def make_svg(report, anchors):
    plot_left, plot_right = 136, 810
    operations = report["operations"]

    def x(gate):
        return plot_left + (plot_right - plot_left) * gate / (operations - 1)

    chart = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="860" height="344" '
        'viewBox="0 0 860 344" role="img" aria-labelledby="title description">',
        '<title id="title">Ancilla lifetimes at forced invsqrt width-46 cuts</title>',
        '<desc id="description">Physical gate indices of every forced width-46 '
        'cut and the four ancilla lifetimes shared by all cuts.</desc>',
        '<rect width="860" height="344" fill="#fff"/>',
        '<g font-family="system-ui,sans-serif" fill="#192e39">',
        '<text x="26" y="38" font-size="23" font-weight="650">invsqrt width-46 cuts</text>',
        f'<text x="26" y="63" font-size="14">{report["forced_cuts"]:,} cuts · '
        f'{report["distinct_live_sets"]:,} distinct live sets · '
        f'{report["operations"]:,} circuit operations</text>',
        '<text x="26" y="106" font-size="13">Forced cuts</text>',
        '<text x="26" y="158" font-size="13">Shared ancilla</text>',
    ]
    ticks = [0, 5000, 10000, 15000, 20000, operations - 1]
    for tick in ticks:
        horizontal = x(tick)
        chart.append(f'<path d="M{horizontal:.4f} 86v202" stroke="#d9e1e5"/>')
        chart.append(f'<text x="{horizontal:.4f}" y="308" text-anchor="middle" '
                     f'font-size="12">{tick:,}</text>')
    chart.append('<text x="473" y="331" text-anchor="middle" '
                 'font-size="13">Gate index after omitting register declarations</text>')
    dashes = [0]
    previous_end = 0
    for _, group in groupby(enumerate(anchors), key=lambda entry: entry[1] - entry[0]):
        run = [anchor for _, anchor in group]
        start, end = run[0], run[-1] + 1
        dashes.extend([start - previous_end, end - start])
        previous_end = end
    dashes.append(operations - previous_end)
    dash_array = " ".join(map(str, dashes))
    chart.append(f'<path d="M{plot_left} 103H{plot_right}" pathLength="{operations - 1}" '
                 f'fill="none" stroke="#b74435" stroke-width="22" stroke-dasharray="{dash_array}"/>')
    for row, record in enumerate(report["common_lifetimes"]):
        start, end = record["birth"], record["death"]
        y = 178 + 30 * row
        title = escape(f'{record["wire"]} [{start:,}, {end:,}): '
                       f'{record["birth_gate"]} → {record["death_gate"]}')
        chart.append(f'<g><title>{title}</title>'
                     f'<text x="98" y="{y + 4}" font-size="13">{record["wire"]}</text>'
                     f'<path d="M{x(start):.4f} {y}H{x(end):.4f}" stroke="#176a70" stroke-width="5"/>'
                     f'<path d="M{x(start):.4f} {y-5}v10M{x(end):.4f} {y-5}v10" '
                     'stroke="#0e4b4e" stroke-width="1.5"/></g>')
    chart.append('</g></svg>')
    return "\n".join(chart) + "\n"


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()
    report, anchors = scan(args.source)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    if args.svg:
        args.svg.write_text(make_svg(report, anchors))


if __name__ == "__main__":
    main()
