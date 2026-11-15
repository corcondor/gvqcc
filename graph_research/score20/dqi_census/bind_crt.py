"""Match a checked CRT prefix to e4 and optionally splice the intermediate."""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import sys

from census import PIN, digest, open_columns


def write_bound_prefix(circuit, output, start, stop, before, after, binary, encode):
    """Splice a complete checked component, preserving all other columns."""
    original, replacement = encode(before), encode(after)
    cuts = {}
    lengths = {kind: packet["payload_bytes"] for kind, packet in circuit.packets.items()}
    for kind in range(1, 11):
        a, b = circuit.column_range(kind, start, stop)
        offset = circuit.packets[kind]["payload_offset"]
        assert circuit.data[offset + a:offset + b] == original[kind]
        cuts[kind] = (a, b)
        lengths[kind] += len(replacement[kind]) - (b - a)
    fields = dict(circuit.profile["header"])
    for field, kind, width in (
        ("num_ops", 1, 1), ("num_ops_with_3_target_qubits", 2, 4),
        ("num_ops_with_2_target_qubits", 5, 4), ("num_ops_with_1_target_qubits", 7, 4),
        ("num_ops_with_1_target_bit", 8, 4), ("num_ops_with_1_condition_bit", 9, 4),
        ("num_ops_with_angle", 10, 16),
    ):
        fields[field] = lengths[kind] // width
    fmt = binary.kp
    with output.open("xb") as stream:
        stream.write(fmt.HEADER.pack(fmt.MAGIC, *(fields[key] for key in fmt.HEADER_FIELDS)))
        first_packet = circuit.packets[1]["payload_offset"] - fmt.PACKET.size
        binary.copy_range(circuit.data, stream, fmt.HEADER.size, first_packet)
        for kind in range(1, 12):
            packet = circuit.packets[kind]
            base = packet["payload_offset"]
            stream.write(fmt.PACKET.pack(kind, lengths[kind]))
            if kind not in cuts:
                binary.copy_range(circuit.data, stream, base, base + packet["payload_bytes"])
                continue
            a, b = cuts[kind]
            binary.copy_range(circuit.data, stream, base, base + a)
            stream.write(replacement[kind])
            binary.copy_range(circuit.data, stream, base + b, base + packet["payload_bytes"])


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--prior-code", type=Path, required=True)
    parser.add_argument("--output-kmb", type=Path)
    args = parser.parse_args()
    assert digest(args.source) == PIN
    sys.path.insert(0, str(args.prior_code))
    import dqi_ccx_peephole as binary
    import kmb_profile
    from outcome_dqi_chart_match import match
    from outcome_dqi_chart_splice_norm import encode

    def open_path(path):
        return open_columns(path, binary.BinaryCircuit, kmb_profile)

    base = open_path(args.source)
    native = json.loads((args.native / "result.json").read_text())
    old = open_path(args.native / "original_prefix.kmb")
    new = open_path(args.native / "split_prefix.kmb")
    for case, block in (("original_prefix", old), ("split_prefix", new)):
        entry = next(row for row in native["rows"] if row["case"] == case)
        assert digest(block.path) == entry["sha256"]
    prior = list(old.operations(0, len(old.opcodes)))
    replacement = list(new.operations(0, len(new.opcodes)))
    end = 0
    ranges = []
    blocks = []
    while (position := base.opcodes.find(old.opcodes, end)) >= 0:
        end = position + 1
        stop = position + len(old.opcodes)
        region = list(base.operations(position, stop))
        maps = match(prior, region)
        if maps is None:
            continue

        def classical_trace(sequence):
            return [(op.opcode, op.bit, op.condition) for op in sequence
                    if op.bit is not None or op.condition is not None]

        assert classical_trace(prior) == classical_trace(replacement)
        assert {q for op in prior for q in op.qubits} == {q for op in replacement for q in op.qubits}
        assert set(Counter(op.opcode for op in prior)) == set(Counter(op.opcode for op in replacement))
        assert sum(op.is_ccx for op in replacement) - sum(op.is_ccx for op in prior) == 15
        qubits, bits = maps["qubits"], maps["bits"]
        mapped = [binary.Operation(op.opcode, tuple(qubits[q] for q in op.qubits),
                                   bits[op.bit] if op.bit is not None else None,
                                   bits[op.condition] if op.condition is not None else None, op.angle)
                  for op in replacement]
        ranges.append(dict(start=position, end=stop, new_start=position,
                           new_end=position + len(mapped), wire_map=maps["qubits"]))
        blocks.append((position, stop, region, mapped))
    report = dict(source_sha256=PIN, degree=native["degree"], node=native["node"],
                  exact_sites=len(ranges), matches=ranges, whole_quantum_width=889,
                  paired_native_shots=[row["native_shots"] for row in native["rows"]],
                  old_ops=len(old.opcodes), new_ops=len(new.opcodes),
                  static_unconditional_ccx_delta=15 * len(blocks))
    if args.output_kmb is not None:
        assert len(blocks) == 1, "This intermediate splicer requires one unique site"
        write_bound_prefix(base, args.output_kmb, *blocks[0], binary, encode)
        report["candidate_sha256"] = digest(args.output_kmb)
        report["candidate_path"] = str(args.output_kmb)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print({**report, "matches": [(row["start"], row["end"]) for row in ranges]}, flush=True)
    new.close()
    old.close()
    base.close()


if __name__ == "__main__":
    main()
