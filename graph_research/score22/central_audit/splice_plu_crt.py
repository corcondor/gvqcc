"""Bind the narrow CRT compute/return pair by exact opcodes and operands."""

from argparse import ArgumentParser
from hashlib import file_digest
import json
from pathlib import Path
import sys

import numpy as np

from census import digest, open_columns


def locate(base, reference, lo, hi, match):
    pattern = reference.opcodes[lo:hi]
    before = list(reference.operations(lo, hi))
    results = []
    pos = 0
    while (candidate := base.opcodes.find(pattern, pos)) >= 0:
        pos = candidate + 1
        end = candidate + len(pattern)
        if (mapping := match(before, base.operations(candidate, end))) is not None:
            results.append((candidate, end, mapping))
    assert len(results) == 1, f"Expected one exact component match, got {len(results)}"
    return results[0]


def audit_retired_bits(base, original_prefix, original_return, before_close, close,
                       exported):
    writes = {int(op.bit) for op in original_return if op.bit is not None}
    assert {op.bit for op in original_prefix if op.bit is not None} == set(exported)
    interesting = np.array(sorted(writes | set(exported)), dtype=np.uint32)
    opcodes = np.frombuffer(base.opcodes, dtype=np.uint8)
    positioned = []
    for column, flag, is_write in ((8, 0x40, True), (9, 0x80, False)):
        packet = base.packets[column]
        options = np.frombuffer(base.data, dtype="<u4", offset=packet["payload_offset"],
                                count=packet["payload_bytes"] // 4)
        positions = np.flatnonzero(opcodes & flag)
        assert len(positions) == len(options)
        hits = np.flatnonzero(np.isin(options, interesting))
        positioned.extend((int(positions[k]), int(options[k]), is_write) for k in hits)
        del options
    positioned.sort()
    # Output P mask is opaque between the exact prefix and its bound closing.
    assert not any(before_close <= p < close[0] and bit in exported for p, bit, _ in positioned)
    after = {}
    for index, bit, is_write in positioned:
        if index >= close[1] and bit not in after:
            after[bit] = (index, is_write)
    required = writes | set(exported)
    pushes = np.flatnonzero(opcodes == 0x81)
    pops = np.flatnonzero(opcodes == 0x01)
    for bit in required:
        if bit not in after:
            continue
        index, is_write = after[bit]
        assert (is_write and base.opcodes[index] in (0x40, 0x41, 0x50)
                and np.searchsorted(pushes, index) == np.searchsorted(pops, index)), (index, bit)
    return len(required)


def translate_bound_block(original, latest, region, sites, compare_ranges):
    start, stop, mapping = region
    current = start + sum((item["new_end"] - item["new_start"])
                          - (item["old_end"] - item["old_start"])
                          for item in sites if item["old_end"] <= start)
    cursor = start
    new_start = current
    consumed = []
    for item in sites:
        a, b = item["old_start"], item["old_end"]
        if a >= stop or b <= start:
            continue
        assert cursor <= a < b <= stop
        assert current + a - cursor == item["new_start"]
        assert compare_ranges(original, cursor, a, latest, current, item["new_start"])["equal"]
        current = item["new_end"]
        cursor = b
        consumed.append(item)
    new_stop = current + stop - cursor
    assert compare_ranges(original, cursor, stop, latest, current, new_stop)["equal"]
    return (new_start, new_stop, mapping), consumed


def write_patches(circuit, output, patches, binary, encode, n_bits):
    lengths = {name: col["payload_bytes"] for name, col in circuit.packets.items()}
    spans = {name: [] for name in range(1, 11)}
    for start, stop, replacement in patches:
        data = encode(replacement)
        for kind in range(1, 11):
            a, b = circuit.column_range(kind, start, stop)
            spans[kind].append((a, b, data[kind]))
            lengths[kind] += len(data[kind]) - (b - a)
    fields = dict(circuit.profile["header"])
    fields["num_bits"] = n_bits
    for key, kind, width in (
        ("num_ops", 1, 1), ("num_ops_with_3_target_qubits", 2, 4),
        ("num_ops_with_2_target_qubits", 5, 4), ("num_ops_with_1_target_qubits", 7, 4),
        ("num_ops_with_1_target_bit", 8, 4), ("num_ops_with_1_condition_bit", 9, 4),
        ("num_ops_with_angle", 10, 16),
    ):
        fields[key] = lengths[kind] // width
    fmt = binary.kp
    with output.open("xb") as stream:
        stream.write(fmt.HEADER.pack(fmt.MAGIC, *(fields[k] for k in fmt.HEADER_FIELDS)))
        first = circuit.packets[1]["payload_offset"] - fmt.PACKET.size
        binary.copy_range(circuit.data, stream, fmt.HEADER.size, first)
        for kind in range(1, 12):
            packet = circuit.packets[kind]
            offset = packet["payload_offset"]
            stream.write(fmt.PACKET.pack(kind, lengths[kind]))
            cursor = 0
            for a, b, payload in spans.get(kind, ()):
                assert cursor <= a
                binary.copy_range(circuit.data, stream, offset + cursor, offset + a)
                stream.write(payload)
                cursor = b
            binary.copy_range(circuit.data, stream, offset + cursor, offset + packet["payload_bytes"])
    return fields


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("native", type=Path)
    cli.add_argument("report", type=Path)
    cli.add_argument("--source-sha", required=True)
    cli.add_argument("--prior-code", type=Path, required=True)
    cli.add_argument("--output-kmb", type=Path)
    cli.add_argument("--old-reference", type=Path)
    cli.add_argument("--overlay-receipt", type=Path)
    args = cli.parse_args()
    assert digest(args.source) == args.source_sha
    sys.path.insert(0, str(args.prior_code))
    import dqi_ccx_peephole as binary
    import kmb_profile
    from kmb_splice import compare_ranges
    from outcome_dqi_chart_match import match
    from outcome_dqi_chart_splice_norm import encode

    def open_path(path):
        return open_columns(path, binary.BinaryCircuit, kmb_profile)

    ready = json.loads((args.native / "result.json").read_text())
    receipts = {row["case"]: row for row in ready["rows"]}
    base = open_path(args.source)
    old = open_path(args.native / "original_closed.kmb")
    new = open_path(args.native / "plu_closed.kmb")
    for name, obj in (("original_closed", old), ("plu_closed", new)):
        assert digest(obj.path) == receipts[name]["sha256"]
    a, b = receipts["original_closed"], receipts["plu_closed"]
    original = [(0, a["prefix_ops"]), (a["marks"]["begin_return"], a["operations"])]
    changed = [(0, b["prefix_ops"]), (b["marks"]["begin_return"], b["operations"])]
    consumed = []
    if args.old_reference is not None:
        from census import PIN

        assert args.overlay_receipt is not None and digest(args.old_reference) == PIN
        overlay = json.loads(args.overlay_receipt.read_text())["output"]
        assert overlay["sha256"] == args.source_sha
        reference = open_path(args.old_reference)
        translated = []
        for x, y in original:
            bound = locate(reference, old, x, y, match)
            replacement_bound, overlaps = translate_bound_block(
                reference, base, bound, overlay["sites"], compare_ranges)
            translated.append(replacement_bound)
            consumed.extend(overlaps)
        pre, ret = translated
        reference.close()
    else:
        pre, ret = [locate(base, old, x, y, match) for x, y in original]
    assert pre[1] < ret[0]
    print("Bound source sites", pre[:2], ret[:2], flush=True)
    prior_debt = a["old_target_mask_ids"]
    fresh_debt = b["old_target_mask_ids"]
    exported = [pre[2]["bits"][idx] for idx in prior_debt]
    assert exported == [ret[2]["bits"][idx] for idx in prior_debt]
    data = (2 * ready["degree"] + 3) * 12
    assert all(pre[2]["qubits"][q] == ret[2]["qubits"][q] for q in range(data))
    before = [list(base.operations(x, y)) for x, y, _ in (pre, ret)]
    dead = audit_retired_bits(base, *before, pre[1], ret, set(exported))
    new_bitmap = dict(zip(fresh_debt, exported))
    next_bit = base.profile["header"]["num_bits"]
    patches = []
    splice_ranges = []
    offset = 0
    for hit, (lo, hi) in zip((pre, ret), changed):
        start, stop, maps = hit
        mapped = []

        def bidx(index):
            nonlocal next_bit
            if index is None:
                return None
            if index not in new_bitmap:
                new_bitmap[index] = next_bit
                next_bit += 1
            return new_bitmap[index]

        for op in new.operations(lo, hi):
            mapped.append(binary.Operation(op.opcode, tuple(maps["qubits"][q] for q in op.qubits),
                                          bidx(op.bit), bidx(op.condition), op.angle))
        patches.append((start, stop, mapped))
        splice_ranges.append(dict(old_start=start, old_end=stop, new_start=start + offset,
                                  new_end=start + offset + len(mapped)))
        offset += len(mapped) - (stop - start)
    report = dict(source_sha256=args.source_sha, r=ready["degree"], node=ready["node"],
                  matches=splice_ranges, classical_output_mask_ids=exported,
                  absorbed_exact_overlay_sites=consumed,
                  retired_classical_bits_checked=dead, whole_width=base.profile["header"]["num_qubits"],
                  degree34_local_helper_width=[a["helper_peak"], b["helper_peak"]],
                  static_T_delta=b["static_T"] - a["static_T"],
                  stock_verifier_ran=False)
    if args.output_kmb is not None:
        report["output_header"] = write_patches(base, args.output_kmb, patches, binary,
                                                  encode, next_bit)
        report["output_sha256"] = digest(args.output_kmb)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(report, flush=True)
    new.close()
    old.close()
    base.close()


if __name__ == "__main__":
    main()
