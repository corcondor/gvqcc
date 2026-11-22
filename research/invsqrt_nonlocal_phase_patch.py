#!/usr/bin/env python3
"""Rebuild experimentally phase-equivalent invsqrt 9T->4S candidate.

Uses existing gvqcc KMB profile/splice implementation. NOT official value/phase
certification. The two late nonlocal gadgets are original; the early 3T->2S
gadget is from the public varianceofx implementation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import kmb_profile as kp
from dqi_ccx_peephole import BinaryCircuit, Operation, write_rewritten

SOURCE_SHA = 'd2148a7cd7a4d0a004eca1e7b18f9fd1282df4ed3be4a9aa970842f9119fa307'
OUTPUT_SHA = 'f9f00359d591bb0c9ec07d8d216efcc6086521ccd123f00796e0a6f84bd52452'
REMOVALS = {223:31, 232:0, 234:0, 32662:13, 32663:14, 32665:14,
            34341:20, 34342:26, 34344:26}
INSERTIONS = {8145:(35,+1), 8344:(36,+1), 10063:(31,-1), 21002:(33,+1)}


def patch(source: Path, output: Path):
    if output.exists() or source.resolve() == output.resolve():
        raise FileExistsError('Refuse output overwrite or in-place modification')
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if sha != SOURCE_SHA:
        raise ValueError('Wrong input SHA: ' + sha)
    c = BinaryCircuit(source, kp.profile(source, max_register_summaries=0))
    try:
        edits = []
        for i, wire in REMOVALS.items():
            op = next(c.operations(i, i+1))
            val = int.from_bytes(op.angle, 'little', signed=True)
            if op.opcode != 19 or op.qubits != (wire,) or abs(val) != 2**125:
                raise ValueError(('Source T rotation mismatch', i, op))
            edits.append((i, i+1, [op], []))
        for i, (wire, sign) in INSERTIONS.items():
            new = Operation(0x13, (wire,), angle=(sign * 2**126).to_bytes(16,'little',signed=True))
            edits.append((i+1, i+1, [], [new]))
        write_rewritten(c, output, sorted(edits))
    finally:
        c.close()
    got = hashlib.sha256(output.read_bytes()).hexdigest()
    if got != OUTPUT_SHA:
        output.unlink(missing_ok=True)
        raise AssertionError(('Output SHA mismatch', got, OUTPUT_SHA))
    return {'status':'COMPILED_ONLY_NOT_OFFICIAL_VERIFIED', 'input_sha256':sha,
            'candidate_sha256':got, 'removed_T':9, 'inserted_S':4,
            'qubits':37, 'CCX_unchanged':1470,
            'certification':'Exhaustive domain differential phase proved separately; official KickMix NOT RUN'}


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source',type=Path)
    a.add_argument('output',type=Path)
    args = a.parse_args()
    print(json.dumps(patch(args.source,args.output),indent=2))


if __name__ == '__main__':
    main()
