"""Render the pinned cache route and a projected gate-dependency graph."""
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess


def quoted(value):
    return json.dumps(value, ensure_ascii=False)


def node(name, label, color="#EEF3F9", **attrs):
    options = {
        "label": label,
        "fillcolor": color,
        **attrs,
    }
    return f'{name} [{", ".join(f"{key}={quoted(value)}" for key,value in options.items())}];'


def graph_header(name, title, rankdir):
    return [
        f'digraph {name} {{',
        f'graph [rankdir={rankdir}, bgcolor="#F8FAFD", pad="0.28", nodesep="0.28", '
        f'ranksep="0.42", label={quoted(title)}, labelloc=t, labeljust=l, '
        'fontname="Noto Sans CJK JP", fontsize=17, fontcolor="#172849"];',
        'node [shape=box, fontname="Noto Sans CJK JP", fontsize=11, color="#8EA2B9", '
        'margin="0.15,0.08", style="rounded,filled", fontcolor="#172849"];',
        'edge [fontname="Noto Sans CJK JP", fontsize=9, color="#506A89", '
        'fontcolor="#344D6C", arrowsize="0.72"];',
    ]


def pair_label(features):
    return "{" + ", ".join(f"f{i}" for i in features) + "}"


def exchange_dot(slice_info):
    move = slice_info["cache_move"]
    start, end = slice_info["kmx_text_rows_inclusive_1_based"]
    old = move["evicted"][0]
    new = move["restored"][0]
    left, right, output = slice_info["control_and_output_wires"]
    q = old["wire"]
    x, y = [f"q{k}" for k in old["controls"]]
    a, b = [f"q{k}" for k in new["controls"]]
    left_sources = len(slice_info["cx_sources_by_control_wire"][str(left)])
    right_sources = len(slice_info["cx_sources_by_control_wire"][str(right)])
    fanout = len(slice_info["fanout_targets_updated_before_ccx"])
    title = f"ANGLE k=13 ｜KMX {start}–{end}行の値・位相依存"
    dot = graph_header("exchange", title, "TB")
    dot += [
        node("old", f"旧 q{q} = {x} ∧ {y}\n特徴量 f{old['feature']}", "#FFEAC9"),
        node("hmr", f"{start}  HMR q{q} b0", "#FFEAC9"),
        node("zero", f"q{q} のリセット後\n|0⟩", "#EEF3F9"),
        node("phase_inputs", f"保持線 {x}, {y}", "#DDEBF8"),
        node("cz", f"{start + 1}  CZ {x} {y} if b0\n測定の位相を相殺", "#FFEAC9"),
        node("live", f"保持線 {a}, {b}", "#DDEBF8"),
        node("remat", f"{start + 2}  CCX {a} {b} q{q}\n特徴量 f{new['feature']} を再生成", "#CEEFE1"),
        node("left", f"制御 q{left}\nCX {left_sources}本でパリティを組む", "#DDEBF8"),
        node("right", f"制御 q{right}\nCX {right_sources}本でパリティを組む", "#DDEBF8"),
        node("out", f"{end}  CCX q{left} q{right} q{output}", "#CEEFE1"),
        node("fanout", f"出力基底の準備\nq{output} から CX {fanout}本", "#F2E8FC"),
        "old -> hmr;",
        'hmr -> cz [label="古典 b0", style=dashed, color="#9A5F19"];',
        "phase_inputs -> cz;",
        "hmr -> zero;",
        "zero -> remat;",
        'cz -> remat [label="命令順", style=dotted];',
        "live -> remat;",
        f'remat -> left [label="{start+3}  CX q{q} q{left}"];',
        "remat -> right;",
        "left -> out;",
        "right -> out;",
        'fanout -> out [label="先に実行", style=dotted];',
        "}",
    ]
    return "\n".join(dot) + "\n"


def route_dot(route):
    selected = route["selected"]
    dot = graph_header("route", "ANGLE k=13 ｜選択された欠損ペアの経路", "TB")
    dot += [node("s0", f"開始  {pair_label(selected['missing_start'])}", "#E5EDFC")]
    for move in route["moves"]:
        i = move["group"]
        pair = pair_label(move["missing_to"])
        terms = len(move["product_ids_zero_based"])
        affine = len(move["affine_ids_zero_based"])
        suffix = f"積 {terms} ｜線形補正 {affine}"
        if move["terminal_cleanup"]:
            label = f"終了  {pair}\nこの配置でアンコンピュート"
            color = "#E5EDFC"
        else:
            label = f"グループ {i}  {pair}\n{suffix}"
            color = "#CEEFE1" if i == 3 else "#EEF3F9"
        dot += [
            node(f"s{i}", label, color),
            f's{i-1} -> s{i} [label={quoted(f"再生成 CCX +{move['rematerialized']}")}];',
        ]
    return "\n".join(dot + ["}"]) + "\n"


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--png", action="store_true")
    args = parser.parse_args()
    directory = args.directory
    route = json.loads((directory / "angle_route.json").read_text())
    detail = json.loads((directory / "angle_slice.json").read_text())
    assert route["sha256"] == detail["sha256"]
    drawings = {"angle_exchange": exchange_dot(detail), "angle_route": route_dot(route)}
    for name, text in drawings.items():
        dot = directory / f"{name}.dot"
        dot.write_text(text)
        output_formats = ("svg", "png") if args.png else ("svg",)
        for fmt in output_formats:
            subprocess.run(["dot", f"-T{fmt}", str(dot), "-o", str(directory / f"{name}.{fmt}")],
                           check=True)


if __name__ == "__main__":
    main()
