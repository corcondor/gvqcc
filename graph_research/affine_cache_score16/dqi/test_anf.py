"""Control fixtures for phase-aware sparse-polynomial simplification."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile

MAGIC = bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
HEADER = struct.Struct("<16s4I9Q")
PACKET = struct.Struct("<QQ")


def make_circuit(path, ops):
    q = 844
    data = [bytearray() for _ in range(12)]
    counts = [len(ops)] + [0] * 8
    for code, operands, bit, cond in ops:
        arity = len(operands)
        assert arity == ((code >> 4) & 3)
        data[1].append(code)
        if arity:
            counts[4 - arity] += 1
        for j, wire in enumerate(operands):
            column = {3: 2, 2: 5, 1: 7}[arity]
            data[column + j].extend(struct.pack("<I", wire))
        if code & 64:
            data[8].extend(struct.pack("<I", bit))
            counts[4] += 1
        if code & 128:
            data[9].extend(struct.pack("<I", cond))
            counts[5] += 1
    stream = HEADER.pack(MAGIC, 2, q, 1, 0, *counts)
    for i in range(1, 12):
        stream += PACKET.pack(i, len(data[i])) + data[i]
    path.write_bytes(stream)


def op(code, *wires, bit=None, cond=None):
    return code, wires, bit, cond


multiply = [
    op(0x31, 0, 1, 840),
    op(0x21, 0, 841),
    op(0x21, 1, 841),
]
nested = [
    op(0x50, 841, bit=0),
    op(0x81, cond=0),
    op(0x21, 0, 840),
    op(0x01),
]
tests = {
    "expanded_cross_terms": (
        multiply + [op(0x31, 840, 841, 842)],
        [[3, "DELETE"]],
    ),
    "phase_after_anded_variables": (
        multiply + [op(0x30, 840, 0, 1)],
        [[3, "Z0"]],
    ),
    "conditional_swap_of_equal_inputs": (
        multiply + [op(0x32, 840, 0, 1)],
        [[3, "DELETE"]],
    ),
    "dependent_join_at_scope_exit": (
        nested + [op(0x31, 840, 0, 842)],
        [[4, "CX0"]],
    ),
    "non_equivalent_join": (
        nested + [op(0x31, 840, 1, 842)],
        [],
    ),
    "independent_abi_inputs": (
        [op(0x31, 0, 1, 842)],
        [],
    ),
}
if __name__ == "__main__":
    import sys

    with tempfile.TemporaryDirectory() as work:
        temp = Path(work)
        checks = {}
        for label, (ops, expect) in tests.items():
            fixture = temp / "test.kmb"
            result = temp / "hits.tsv"
            make_circuit(fixture, ops)
            subprocess.run([sys.argv[1], str(fixture), str(result)], check=True, capture_output=True)
            got = [
                [int(line.split("\t")[0]), line.split("\t")[-1]]
                for line in result.read_text().splitlines()[1:]
            ]
            assert got == expect, (label, got, expect)
            checks[label] = got
        print(json.dumps(checks, indent=2))
