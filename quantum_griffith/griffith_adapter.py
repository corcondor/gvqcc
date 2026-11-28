"""Strict adapter for Griffith's hard Boolean IR to Quantum Griffith.

Supported:
  - one input port, a sequential chain of 1/2-input lut_layer nodes
  - optional terminal group_sum (its PRE-classification *bits* are exported)
  - deploy-time lut_flat nodes, including constant/negative-polarity references
Unsupported layouts fail loudly (multi-input DAG, 4/6-input LUTs, conv, arithmetic,
npz sidecars and GroupSum class-score oracle semantics). Use Griffith's own
lower_to_primitives for native 4/6-input/conv networks before conversion.

Reference: https://github.com/tsukushi-gate/Griffith
           docs-site/src/content/docs/reference/ir-schema.md
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping

from .logic_dag import LogicDAG, LogicGate, lower_logic_dag
from .reversible import Circuit


class UnsupportedGriffithIR(ValueError):
    """The IR is valid or plausible Griffith IR but not supported by adapter."""


def _binary_table(table: Any, arity: int) -> int:
    try:
        tt = int(table, 0) if isinstance(table, str) else int(table)
    except (TypeError, ValueError) as exc:
        raise UnsupportedGriffithIR("Invalid truth table") from exc
    if tt < 0 or tt >= (1 << (1 << arity)):
        raise UnsupportedGriffithIR("Truth table outside arity range")
    return tt


def _indices(params: dict, arity: int, width: int, previous: int):
    rows = params.get("indices")
    if not isinstance(rows, list):
        raise UnsupportedGriffithIR("Use Griffith load_ir to resolve .npz sidecars first")
    if len(rows) != arity or not all(isinstance(r, list) and len(r) == width for r in rows):
        raise UnsupportedGriffithIR("Bad indices shape")
    if any(not isinstance(i, int) or i < 0 or i >= previous for r in rows for i in r):
        raise UnsupportedGriffithIR("Index out of range")
    return rows


def from_griffith_ir(document: Mapping[str, Any]) -> LogicDAG:
    """Lower a small serial Griffith JSON IR to a pure Boolean DAG.

    GroupSum maps bits to integer logits and is not a Boolean oracle. If the
    last node is GroupSum, the adapter intentionally exposes its input bits
    and never claims to preserve the class-score/argmax behavior.
    """
    if document.get("format") != "magicdelta-ir":
        raise UnsupportedGriffithIR("Expected Griffith magicdelta-ir JSON")
    inputs = document.get("inputs", [])
    nodes = document.get("nodes", [])
    outputs = document.get("outputs", [])
    edges = document.get("edges", [])
    if len(inputs) != 1 or len(outputs) != 1:
        raise UnsupportedGriffithIR("Only one input and output port supported")
    n_inputs = inputs[0].get("width", 0)
    if not isinstance(n_inputs, int) or n_inputs < 1:
        raise UnsupportedGriffithIR("Invalid input width")
    if not isinstance(nodes, list) or not nodes:
        raise UnsupportedGriffithIR("Empty or invalid IR")
    if not isinstance(edges, list):
        raise UnsupportedGriffithIR("Expected explicit IR edges")
    incoming: dict[str, str] = {}
    for edge in edges:
        dst, src = edge.get("dst"), edge.get("src")
        if dst in incoming:
            raise UnsupportedGriffithIR("Branches or multiple incoming edges unsupported")
        incoming[dst] = src
    if incoming.get(nodes[0].get("id")) != inputs[0].get("id"):
        raise UnsupportedGriffithIR("First layer must consume input port")
    if incoming.get(outputs[0].get("id")) != nodes[-1].get("id"):
        raise UnsupportedGriffithIR("Output port must follow last node")
    previous_id = inputs[0].get("id")
    previous = list(range(n_inputs))
    gates: list[LogicGate] = []
    saw_group_sum = False

    for position, node in enumerate(nodes):
        kind = node.get("type")
        ident = node.get("id")
        if incoming.get(ident) != previous_id:
            raise UnsupportedGriffithIR("Only explicitly wired serial layers supported")
        if kind == "group_sum":
            if position != len(nodes) - 1 or int(node["params"]["in_width"]) != len(previous):
                raise UnsupportedGriffithIR("Only a terminal GroupSum is supported")
            saw_group_sum = True
            previous_id = ident
            continue
        if saw_group_sum:
            raise UnsupportedGriffithIR("Layer after GroupSum not supported")
        params = node.get("params", {})
        in_width = params.get("in_width")
        out_width = params.get("out_width")
        if in_width != len(previous) or not isinstance(out_width, int) or out_width < 1:
            raise UnsupportedGriffithIR("LUT widths do not match preceding layer")
        next_refs = []
        if kind == "lut_layer":
            arity = params.get("n_inputs")
            if arity not in (1, 2):
                raise UnsupportedGriffithIR(
                    "Only arity 1/2 supported; first lower larger LUTs in Griffith"
                )
            indices = _indices(params, arity, out_width, len(previous))
            tts = params.get("truth_tables", [])
            if len(tts) != out_width:
                raise UnsupportedGriffithIR("Truth table count mismatch")
            for j in range(out_width):
                a = previous[indices[0][j]]
                tt = _binary_table(tts[j], arity)
                if arity == 1:
                    # When a=b, only truth-table addresses 0 and 3 are read.
                    tt = (tt & 1) | (((tt >> 1) & 1) << 3)
                    b = a
                else:
                    b = previous[indices[1][j]]
                next_refs.append(n_inputs + len(gates))
                gates.append(LogicGate(a, b, tt))
        elif kind == "lut_flat":
            triples = params.get("gates", [])
            refs = params.get("outputs", [])
            if not isinstance(triples, list) or len(refs) != out_width:
                raise UnsupportedGriffithIR("Bad lut_flat gate/output arrays")
            # Flat signal 0 is the constant zero; inputs are 1-based.
            zero_ref = n_inputs + len(gates)
            gates.append(LogicGate(0, 0, 0))
            signals = [zero_ref] + list(previous)
            for triple in triples:
                if len(triple) != 3:
                    raise UnsupportedGriffithIR("Bad lut_flat triple")
                tt, a, b = [int(v) for v in triple]
                if not 0 <= tt <= 15 or not 0 <= a < len(signals) or not 0 <= b < len(signals):
                    raise UnsupportedGriffithIR("lut_flat gate reference invalid")
                next_signal = n_inputs + len(gates)
                gates.append(LogicGate(signals[a], signals[b], tt))
                signals.append(next_signal)
            for encoded in refs:
                if not isinstance(encoded, int) or encoded < 0 or encoded // 2 >= len(signals):
                    raise UnsupportedGriffithIR("Bad polarized output ref")
                source = signals[encoded // 2]
                if encoded & 1:
                    next_refs.append(n_inputs + len(gates))
                    gates.append(LogicGate(source, source, 0x1))
                else:
                    next_refs.append(source)
        else:
            raise UnsupportedGriffithIR(f"Unsupported node: {kind}")
        previous = next_refs
        previous_id = ident
    return LogicDAG(n_inputs, tuple(gates), tuple(previous))


def load_griffith_ir(path: str | Path) -> LogicDAG:
    return from_griffith_ir(json.loads(Path(path).read_text(encoding="utf-8")))


def compile_griffith_ir(document: Mapping[str, Any], *, verify: bool = True) -> Circuit:
    return lower_logic_dag(from_griffith_ir(document), verify=verify)
