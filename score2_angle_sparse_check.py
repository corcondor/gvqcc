#!/usr/bin/env python3
"""Independent affine-target proof of standalone sparse XOR/adapter circuits.

Each quantum value is represented by 41 exact truth tables over all 2048
addresses: one constant and 40 coefficients of arbitrary initial output bits.
Products are accepted only if at least one factor is independent of those
output bits. HMR records are independent formal variables and every phase
coefficient must vanish before reuse and at completion. Thus the proof covers
all 2^40 targets and all measurement records, without sampling target values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import kickmix as km

from score2_angle_sparse_patch import emit_sparse_operations, conjugation_adapter


def prove_affine_targets(circuit, operations, label):
    ones = (1 << 2048)-1
    zero = (0,) * 41
    def xor(a, b):
        return tuple(x ^ y for x, y in zip(a,b))
    def product(a, b):
        if not any(a[1:]):
            return tuple(a[0] & value for value in b)
        if not any(b[1:]):
            return tuple(b[0] & value for value in a)
        raise AssertionError("Product is nonlinear in unknown target variables")
    state = [zero] * max(63,circuit.num_qubits)
    for bit in range(11):
        state[bit] = (sum(1 << a for a in range(2048) if a >> bit & 1),) + zero[1:]
    for bit in range(40):
        row = [0] * 41
        row[bit+1] = ones
        state[11+bit] = tuple(row)
    expected = list(state)
    for address, op in operations.items():
        if op["kind"] == "xor":
            constant, shear, linear = op["mask"], 0, 0
        else:
            shear, linear, constant = op["shear"], op["linear"], op["translation"]
            offset = op["offset"]
            if op.get("inverse", False):
                offset ^= (linear & constant).bit_count() & 1
            if offset:
                constant ^= shear
        for bit in range(40):
            row = list(expected[11+bit])
            if constant >> bit & 1:
                row[0] ^= 1 << address
            if shear >> bit & 1:
                for input_bit in range(40):
                    if linear >> input_bit & 1:
                        row[input_bit+1] ^= 1 << address
            expected[11+bit] = tuple(row)
    phases, hmr = {}, 0
    for line in str(circuit).splitlines():
        parts = line.split()
        if not parts or parts[0] in {"REGISTER", "APPEND_TO_REGISTER"}:
            continue
        gate = parts[0]
        qubits = [int(word[1:]) for word in parts[1:] if word.startswith("q")]
        condition = int(parts[-1][1:]) if "if" in parts else None
        if gate in {"X", "CX", "CCX", "HMR"} and condition is not None:
            raise AssertionError("Unexpected conditioned state mutation")
        if gate == "X":
            row = list(state[qubits[0]])
            row[0] ^= ones
            state[qubits[0]] = tuple(row)
        elif gate == "CX":
            state[qubits[1]] = xor(state[qubits[1]],state[qubits[0]])
        elif gate == "CCX":
            state[qubits[2]] = xor(state[qubits[2]],product(state[qubits[0]],state[qubits[1]]))
        elif gate == "HMR":
            bit = int(parts[-1][1:])
            if any(phases.get(bit,zero)):
                raise AssertionError("Measurement variable overwritten before phase cancellation")
            phases[bit] = state[qubits[0]]
            state[qubits[0]] = zero
            hmr += 1
        elif gate == "CZ":
            if condition not in phases:
                raise AssertionError("Unknown phase condition")
            phases[condition] = xor(phases[condition],product(state[qubits[0]],state[qubits[1]]))
        else:
            raise AssertionError("Unsupported patch operation: " + line)
    if state != expected:
        raise AssertionError((label,"affine target map mismatch"))
    if any(any(row) for row in phases.values()):
        raise AssertionError((label,"residual measurement phase"))
    return dict(label=label,status="EXACT_PASS",addresses=2048,arbitrary_target_bits=40,
                symbolic_target_coefficients=41,all_target_assignments_covered=True,
                HMR_formal_variables_cancelled=hmr,all_measurement_branches_covered=True,
                selection_restored=True,workspace_zero=True,phase_identically_zero=True,
                ccx=int(circuit.operation_statistics().num_toffoli_like))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    start = time.monotonic()
    cases = [
        ("one_address_all_outputs", {721:dict(kind="xor",mask=(1 << 40)-1)}),
        ("shared_prefix_many_addresses", {a:dict(kind="xor",mask=((a+1)*0x23456789)&((1 << 40)-1))
                                            for a in (0,1,2,3,400,401,1219,2047)}),
    ]
    # These pairs include disjoint old/new differences, requiring a two-input
    # linear predicate rather than a single output-bit predicate.
    pairs = [(7,0,1,0,2), (2047,0x12345678,0x123456f8,0x12345679,0x123456f9)]
    adapters = {a:dict(conjugation_adapter(x,y,xp,yp),inverse=False) for a,x,y,xp,yp in pairs}
    inverse = {a:dict(op,inverse=True) for a,op in adapters.items()}
    cases += [("general_endpoint_adapter",adapters), ("inverse_endpoint_adapter",inverse)]
    rows = []
    for name, operations in cases:
        lines, estimate = emit_sparse_operations(operations)
        circuit = km.Circuit("\n".join(lines)+"\n")
        row = prove_affine_targets(circuit,operations,name)
        if row["ccx"] != estimate["total_ccx"]:
            raise AssertionError("CCX estimate mismatch")
        rows.append(dict(row,estimate=estimate))
    forward,_ = emit_sparse_operations(adapters)
    backward,_ = emit_sparse_operations(inverse)
    rows.append(prove_affine_targets(km.Circuit("\n".join(forward+backward)+"\n"),{},"adapter_inverse_composition"))
    report = dict(status="ALL_EXACT_PASS",checks=rows,
                  scope="Standalone patches only; source ANGLE family has its separate valid1220 reachable-subspace proof",
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  builder_sha256=hashlib.sha256(Path(__file__).with_name("score2_angle_sparse_patch.py").read_bytes()).hexdigest(),
                  seconds=time.monotonic()-start)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
