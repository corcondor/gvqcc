#!/usr/bin/env python3
"""Read-only, bounded-memory profiler for Kickmix binary format version 2.

Primary specification:
https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md

This validates the binary layout, not circuit semantics or competition scores.
No kickmix installation, NumPy, circuit expansion, or quantum simulation is used.
"""

from __future__ import annotations

import argparse
from array import array
from collections import Counter
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import zipfile


MAGIC = bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
HEADER = struct.Struct("<16s4I9Q")
PACKET = struct.Struct("<QQ")
HEADER_FIELDS = (
    "version", "num_qubits", "num_bits", "num_registers", "num_ops",
    "num_ops_with_3_target_qubits", "num_ops_with_2_target_qubits",
    "num_ops_with_1_target_qubits", "num_ops_with_1_target_bit",
    "num_ops_with_1_condition_bit", "num_ops_with_angle",
    "num_info_tags", "num_info_tag_chars",
)
PACKET_NAMES = (
    "REGISTER_TARGETS", "OPERATION_TYPES",
    "QUBIT0_DATA_FOR_3_TARGET_QUBIT_GATES",
    "QUBIT1_DATA_FOR_3_TARGET_QUBIT_GATES",
    "QUBIT2_DATA_FOR_3_TARGET_QUBIT_GATES",
    "QUBIT0_DATA_FOR_2_TARGET_QUBIT_GATES",
    "QUBIT1_DATA_FOR_2_TARGET_QUBIT_GATES",
    "QUBIT0_DATA_FOR_1_TARGET_QUBIT_GATES",
    "BIT0_DATA_FOR_1_TARGET_BIT_GATES",
    "BIT0_DATA_FOR_1_CONDITION_BIT_GATES",
    "ANGLE_DATA_FOR_ROTATION_GATES", "INFO_TAG_DATA",
)
OPCODES = {
    0x00: "NEG", 0x80: "NEG_IF",
    0x01: "POP_CONDITION", 0x81: "PUSH_CONDITION",
    0x10: "Z", 0x90: "Z_IF", 0x11: "X", 0x91: "X_IF",
    0x12: "R", 0x92: "R_IF", 0x13: "Z_POW", 0x93: "Z_POW_IF",
    0x50: "HMR", 0xD0: "HMR_IF",
    0x20: "CZ", 0xA0: "CZ_IF", 0x21: "CX", 0xA1: "CX_IF",
    0x22: "SWAP", 0xA2: "SWAP_IF",
    0x30: "CCZ", 0xB0: "CCZ_IF", 0x31: "CCX", 0xB1: "CCX_IF",
    0x32: "CSWAP", 0xB2: "CSWAP_IF",
    0x40: "BIT_STORE0", 0xC0: "BIT_STORE0_IF",
    0x41: "BIT_STORE1", 0xC1: "BIT_STORE1_IF",
    0x42: "BIT_INVERT", 0xC2: "BIT_INVERT_IF",
    0x06: "INFO_TAG", 0x07: "DEBUG_PRINT_EMPTY",
    0x87: "DEBUG_PRINT_EMPTY_IF", 0x47: "DEBUG_PRINT_C",
    0xC7: "DEBUG_PRINT_C_IF", 0x17: "DEBUG_PRINT_Q",
    0x97: "DEBUG_PRINT_Q_IF",
}
SPEC_URL = (
    "https://github.com/quantumlib/Qualtran/blob/main/"
    "docs/kickmix/kickmix_binary_format.md"
)
MAX_IDS = 500_000_000
NAME_SAMPLE_BYTES = 256
ID_SAMPLE_COUNT = 8


class KmbFormatError(ValueError):
    """The stream is inconsistent with the documented KMB v2 format."""


def require(condition, message):
    if not condition:
        raise KmbFormatError(message)


def exact_read(stream, size, context):
    """Read at most one configured chunk, tolerating ordinary short reads."""
    first = stream.read(size)
    if len(first) == size:
        return first
    result = bytearray(first)
    while len(result) < size:
        more = stream.read(size - len(result))
        if not more:
            raise KmbFormatError(
                f"Truncated {context}: expected {size} bytes, got {len(result)}"
            )
        result.extend(more)
    return bytes(result)


def uint32s(data):
    result = array("I")
    if result.itemsize != 4:
        raise RuntimeError("This Python platform does not have 32-bit array('I').")
    result.frombytes(data)
    if sys.byteorder != "little":
        result.byteswap()
    return result


class Reader:
    def __init__(self, stream, total_bytes, chunk_bytes, progress=False):
        self.stream = stream
        self.total_bytes = total_bytes
        self.chunk_bytes = chunk_bytes
        self.offset = 0
        self.sha256 = hashlib.sha256()
        self.progress = progress
        self.last_progress = time.monotonic()

    def read(self, count, context):
        require(count <= self.chunk_bytes, "Internal error: unbounded read request")
        require(
            self.offset + count <= self.total_bytes,
            f"{context} extends past the end of the input at offset {self.offset}",
        )
        data = exact_read(self.stream, count, context)
        self.offset += count
        self.sha256.update(data)
        now = time.monotonic()
        if self.progress and now - self.last_progress >= 10:
            print(
                f"Read {self.offset:,}/{self.total_bytes:,} KMB bytes "
                f"({100 * self.offset / max(1, self.total_bytes):.1f}%)",
                file=sys.stderr, flush=True,
            )
            self.last_progress = now
        return data

    def chunks(self, count, context, alignment=1):
        require(count % alignment == 0, f"Misaligned {context}")
        step = self.chunk_bytes - self.chunk_bytes % alignment
        while count:
            size = min(step, count)
            yield self.read(size, context)
            count -= size

    def discard(self, count, context):
        for _ in self.chunks(count, context):
            pass

    def packet(self, expected_type, expected_length=None):
        offset = self.offset
        kind, length = PACKET.unpack(self.read(PACKET.size, "packet header"))
        require(
            kind == expected_type,
            f"Wrong packet type at offset {offset}: expected "
            f"{expected_type} ({PACKET_NAMES[expected_type]}), got {kind}",
        )
        require(
            length <= self.total_bytes - self.offset,
            f"Packet {kind} payload length {length} exceeds remaining input",
        )
        if expected_length is not None:
            require(
                length == expected_length,
                f"Packet {kind} has length {length}, expected {expected_length}",
            )
        return {
            "type": kind, "name": PACKET_NAMES[kind],
            "header_offset": offset, "payload_offset": self.offset,
            "payload_bytes": length,
        }


class InputSource:
    """Own the archive for as long as any of its member streams are open."""

    def __init__(self, path, member=None):
        self.path = Path(path).resolve()
        self.member_request = member
        self.archive = None
        self.member_info = None

    def __enter__(self):
        require(self.path.is_file(), f"Input is not a regular file: {self.path}")
        is_zip = (
            self.member_request is not None or self.path.suffix.lower() == ".zip"
            or zipfile.is_zipfile(self.path)
        )
        if is_zip:
            self.archive = zipfile.ZipFile(self.path, "r")
            try:
                entries = [info for info in self.archive.infolist() if not info.is_dir()]
                if self.member_request is not None:
                    matches = [i for i in entries if i.filename == self.member_request]
                else:
                    candidates = [
                        i for i in entries if i.filename.lower().endswith(".kmb")
                    ]
                    dqi = [
                        i for i in candidates
                        if i.filename.rsplit("/", 1)[-1].lower() == "dqi.kmb"
                    ]
                    matches = dqi if dqi else candidates
                require(
                    len(matches) == 1,
                    "ZIP member selection is missing or ambiguous; specify the exact "
                    "member with --member (duplicate names are not supported)",
                )
                self.member_info = matches[0]
                require(
                    not (self.member_info.flag_bits & 1),
                    "Encrypted ZIP members are not supported",
                )
                self.size = self.member_info.file_size
            except BaseException:
                self.archive.close()
                raise
        else:
            self.size = self.path.stat().st_size
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.archive is not None:
            self.archive.close()

    def open(self):
        if self.archive is not None:
            return self.archive.open(self.member_info, "r")
        return self.path.open("rb")

    def describe(self):
        result = {
            "path": str(self.path), "container": "zip" if self.archive else "file",
            "member": self.member_info.filename if self.member_info else None,
            "kmb_bytes": self.size, "container_bytes": self.path.stat().st_size,
        }
        if self.member_info:
            result["member_compressed_bytes"] = self.member_info.compress_size
            result["zip_compression_method"] = self.member_info.compress_type
        return result


def scan_stream(stream, size, chunk_bytes, max_register_summaries, progress=False):
    reader = Reader(stream, size, chunk_bytes, progress)
    unpacked = HEADER.unpack(reader.read(HEADER.size, "KMB header"))
    require(unpacked[0] == MAGIC, "Invalid KMB magic bytes")
    header = dict(zip(HEADER_FIELDS, unpacked[1:]))
    require(header["version"] == 2, f"Unsupported KMB version {header['version']}; require 2")
    for field in ("num_qubits", "num_bits"):
        require(header[field] <= MAX_IDS, f"{field} exceeds the format limit {MAX_IDS}")
    for field in HEADER_FIELDS[5:-1]:
        require(header[field] <= header["num_ops"], f"{field} exceeds num_ops")
    require(
        sum(header[f"num_ops_with_{n}_target_qubits"] for n in (1, 2, 3))
        <= header["num_ops"], "Qubit-arity counts sum to more than num_ops",
    )
    n3 = header["num_ops_with_3_target_qubits"]
    n2 = header["num_ops_with_2_target_qubits"]
    lengths = {
        1: header["num_ops"],
        2: 4 * n3, 3: 4 * n3, 4: 4 * n3,
        5: 4 * n2, 6: 4 * n2,
        7: 4 * header["num_ops_with_1_target_qubits"],
        8: 4 * header["num_ops_with_1_target_bit"],
        9: 4 * header["num_ops_with_1_condition_bit"],
        10: 16 * header["num_ops_with_angle"],
        11: 8 + 8 * header["num_info_tags"] + header["num_info_tag_chars"],
    }
    min_size = (
        HEADER.size + 24 * header["num_registers"]
        + 11 * PACKET.size + sum(lengths.values())
    )
    require(min_size <= size, "Header counts require more bytes than the input contains")
    maxima = {"quantum": -1, "classical": -1}
    register_totals = {
        "count": header["num_registers"], "target_entries": 0,
        "quantum_target_entries": 0, "classical_target_entries": 0,
        "name_bytes": 0, "payload_bytes": 0,
    }
    registers = []
    for index in range(header["num_registers"]):
        packet = reader.packet(0)
        require(packet["payload_bytes"] >= 8, "Register payload is shorter than 8 bytes")
        name_len, reg_len = struct.unpack("<II", reader.read(8, "register sizes"))
        require(
            packet["payload_bytes"] == 8 + name_len + 4 * reg_len,
            f"Register {index} has inconsistent name/target lengths",
        )
        keep = index < max_register_summaries
        prefix = b""
        for data in reader.chunks(name_len, "register name"):
            if keep and len(prefix) < NAME_SAMPLE_BYTES:
                prefix += data[:NAME_SAMPLE_BYTES - len(prefix)]
        nq, nb, maxq, maxb = 0, 0, -1, -1
        sample = []
        for data in reader.chunks(4 * reg_len, "register IDs", 4):
            for raw_id in uint32s(data):
                is_quantum = bool(raw_id & 0x80000000)
                ident = raw_id & 0x7FFFFFFF
                if is_quantum:
                    nq += 1
                    maxq = max(maxq, ident)
                else:
                    nb += 1
                    maxb = max(maxb, ident)
                if keep and len(sample) < ID_SAMPLE_COUNT:
                    sample.append(("q" if is_quantum else "b") + str(ident))
        maxima["quantum"] = max(maxima["quantum"], maxq)
        maxima["classical"] = max(maxima["classical"], maxb)
        register_totals["target_entries"] += reg_len
        register_totals["quantum_target_entries"] += nq
        register_totals["classical_target_entries"] += nb
        register_totals["name_bytes"] += name_len
        register_totals["payload_bytes"] += packet["payload_bytes"]
        if keep:
            registers.append({
                "index": index, "name_utf8_prefix": prefix.decode("utf-8", "replace"),
                "name_prefix_hex": prefix.hex(), "name_bytes": name_len,
                "name_truncated": name_len > len(prefix), "target_entries": reg_len,
                "quantum_target_entries": nq, "classical_target_entries": nb,
                "max_quantum_id": maxq if maxq >= 0 else None,
                "max_classical_id": maxb if maxb >= 0 else None,
                "first_targets": sample,
            })
    packets = {}
    histogram = Counter()
    for kind in range(1, 12):
        packet = reader.packet(kind, lengths[kind])
        packets[kind] = packet
        if kind == 1:
            for data in reader.chunks(lengths[kind], "operation types"):
                histogram.update(data)
            unknown = sorted(set(histogram) - set(OPCODES))
            require(not unknown, f"Undefined operation byte(s): {[hex(x) for x in unknown]}")
            counted = {
                f"num_ops_with_{n}_target_qubits":
                sum(c for op, c in histogram.items() if (op & 0x30) >> 4 == n)
                for n in (1, 2, 3)
            }
            counted.update({
                "num_ops_with_1_target_bit":
                    sum(c for op, c in histogram.items() if op & 0x40),
                "num_ops_with_1_condition_bit":
                    sum(c for op, c in histogram.items() if op & 0x80),
                "num_ops_with_angle": histogram[0x13] + histogram[0x93],
                "num_info_tags": histogram[0x06],
            })
            for field, count in counted.items():
                require(
                    count == header[field],
                    f"{field} is {header[field]} in header but {count} in opcodes",
                )
        elif 2 <= kind <= 9:
            domain = "quantum" if kind <= 7 else "classical"
            maximum = -1
            for data in reader.chunks(lengths[kind], packet["name"], 4):
                maximum = max(maximum, max(uint32s(data), default=-1))
            packet["entries"] = lengths[kind] // 4
            packet["max_id"] = maximum if maximum >= 0 else None
            maxima[domain] = max(maxima[domain], maximum)
        elif kind == 10:
            reader.discard(lengths[kind], "rotation angle data")
            packet["entries"] = header["num_ops_with_angle"]
        else:
            n_tags = struct.unpack("<Q", reader.read(8, "info-tag count"))[0]
            require(n_tags == header["num_info_tags"], "Info-tag count differs from header")
            previous = 0
            for data in reader.chunks(8 * n_tags, "info-tag offsets", 8):
                for (offset,) in struct.iter_unpack("<Q", data):
                    require(
                        previous <= offset <= header["num_info_tag_chars"],
                        "Info-tag offsets are nonmonotonic or exceed character data",
                    )
                    previous = offset
            require(
                previous == header["num_info_tag_chars"],
                "Final info-tag offset differs from num_info_tag_chars",
            )
            reader.discard(header["num_info_tag_chars"], "info-tag characters")
    require(reader.offset == size, f"Unexpected trailing bytes after INFO_TAG_DATA: {size-reader.offset}")
    # Reading through EOF also completes zipfile's CRC checking.
    require(stream.read(1) == b"", "Unexpected bytes beyond the declared source size")
    for domain, field in (("quantum", "num_qubits"), ("classical", "num_bits")):
        require(
            maxima[domain] + 1 == header[field],
            f"{field} is {header[field]} but the largest used {domain} ID is {maxima[domain]}",
        )
    packet_count = header["num_registers"] + 11
    return {
        "header": header,
        "max_quantum_id": maxima["quantum"] if maxima["quantum"] >= 0 else None,
        "max_classical_id": maxima["classical"] if maxima["classical"] >= 0 else None,
        "raw_kmb_sha256": reader.sha256.hexdigest(),
        "registers": {
            "totals": register_totals, "summaries": registers,
            "summaries_omitted": header["num_registers"] - len(registers),
            "counts_are_entries_not_unique_ids": True,
        },
        "opcode_histogram": {
            OPCODES[op]: count for op, count in sorted(histogram.items())
        },
        "opcode_histogram_hex": {
            f"0x{op:02x}": count for op, count in sorted(histogram.items())
        },
        "raw_gate_families": {
            name: {
                "without_explicit_condition": histogram[op],
                "with_explicit_condition": histogram[op | 0x80],
                "total": histogram[op] + histogram[op | 0x80],
            }
            for name, op in (("CCX", 0x31), ("CCZ", 0x30), ("CSWAP", 0x32),
                             ("CX", 0x21), ("HMR", 0x50), ("Z_POW", 0x13))
        },
        "storage": {
            "header_bytes": HEADER.size, "packet_count": packet_count,
            "packet_header_bytes_total": packet_count * PACKET.size,
            "packet_payload_bytes_total": size - HEADER.size - packet_count * PACKET.size,
            "packet_bytes_total": size - HEADER.size,
            "operation_packets": list(packets.values()),
        },
    }, packets


def advance_to(stream, offset, chunk_bytes, is_zip):
    if not is_zip:
        stream.seek(offset)
        return 0
    # Explicit bounded forward reads avoid implementation-dependent ZipExtFile.seek buffering.
    remaining = offset
    while remaining:
        n = min(remaining, chunk_bytes)
        exact_read(stream, n, "ZIP prefix during target verification")
        remaining -= n
    return offset


def verify_disjoint_targets(source, packets, chunk_bytes):
    """Compare separated target columns using a fixed number of stream buffers."""
    additional_bytes_read = 0
    checked = {"two_qubit_operations": 0, "three_qubit_operations": 0}
    for kinds, label in (
        ((2, 3, 4), "three_qubit_operations"), ((5, 6), "two_qubit_operations"),
    ):
        length = packets[kinds[0]]["payload_bytes"]
        if length == 0:
            continue
        with ExitStack() as stack:
            streams = [stack.enter_context(source.open()) for _ in kinds]
            for stream, kind in zip(streams, kinds):
                additional_bytes_read += advance_to(
                    stream, packets[kind]["payload_offset"], chunk_bytes,
                    source.archive is not None,
                )
            remaining = length
            row = 0
            while remaining:
                n = min(chunk_bytes - chunk_bytes % 4, remaining)
                columns = [
                    uint32s(exact_read(stream, n, "gate-target comparison"))
                    for stream in streams
                ]
                additional_bytes_read += n * len(columns)
                for values in zip(*columns):
                    if len(values) == 2:
                        distinct = values[0] != values[1]
                    else:
                        a, b, c = values
                        distinct = a != b and a != c and b != c
                    require(
                        distinct, f"Repeated qubit target in {label} at zero-based row {row}",
                    )
                    row += 1
                remaining -= n
            checked[label] = row
    checked["additional_uncompressed_bytes_read"] = additional_bytes_read
    return checked


def peak_rss_mib():
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round(rss / (1024 * 1024 if sys.platform == "darwin" else 1024), 3)
    except (ImportError, AttributeError):
        return None


def profile(path, member=None, chunk_bytes=1 << 20, max_register_summaries=128, progress=False):
    require(4096 <= chunk_bytes <= 64 * (1 << 20), "Chunk size must be 4 KiB to 64 MiB")
    require(0 <= max_register_summaries <= 10000, "Register summary limit must be 0 to 10000")
    started = time.perf_counter()
    with InputSource(path, member) as source:
        if progress:
            print(f"Profiling {source.describe()}", file=sys.stderr, flush=True)
        with source.open() as stream:
            result, packets = scan_stream(
                stream, source.size, chunk_bytes, max_register_summaries, progress
            )
        if progress:
            print("Checking disjoint 2- and 3-qubit targets.", file=sys.stderr, flush=True)
        disjoint = verify_disjoint_targets(source, packets, chunk_bytes)
        result["source"] = source.describe()
    result.update({
        "schema": "kmb-stream-profile-v1",
        "format_specification": SPEC_URL,
        "validation": {
            "binary_layout": "passed",
            "disjoint_gate_targets": disjoint,
            "semantic_circuit_correctness": "not_checked",
            "condition_stack_semantics": "not_checked",
            "competition_verifier": "not_run",
            "qubit_liveness": "not_computed",
        },
        "interpretation": [
            "Opcode counts are stored instructions, not average executed gate counts.",
            "An operation without an explicit condition can still be inside a condition scope.",
            "Register entries can alias; their sum is not the number of unique qubits.",
            "num_qubits is the maximum referenced ID plus one, not simultaneous live qubits.",
            "No official Toffoli-equivalent cost, task score, or cancellation proof is computed.",
            "The SHA-256 is for raw KMB bytes, not an official normalized circuit hash.",
        ],
        "performance": {
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "process_peak_rss_mib": peak_rss_mib(),
            "chunk_bytes": chunk_bytes,
            "register_summary_limit": max_register_summaries,
            "memory_scaling": "O(chunk_bytes + capped register summaries + ZIP directory metadata)",
            "input_files_modified": False,
        },
    })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Standalone .kmb or a ZIP archive")
    parser.add_argument("--member", help="Exact ZIP member name (e.g. dqi.kmb)")
    parser.add_argument("--output", type=Path, help="Write JSON here; default is stdout")
    parser.add_argument("--chunk-kib", type=int, default=1024, help="Read buffer in KiB (4..65536)")
    parser.add_argument("--max-register-summaries", type=int, default=128)
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr")
    args = parser.parse_args(argv)
    try:
        if args.output is not None:
            require(
                args.output.resolve() != args.input.resolve(),
                "Output must not overwrite the input file",
            )
        result = profile(
            args.input, args.member, args.chunk_kib * 1024,
            args.max_register_summaries, args.progress,
        )
        rendered = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if args.output is not None:
            # Create only after successful validation. Never replace a previous result.
            with args.output.open("x", encoding="utf-8") as output:
                output.write(rendered)
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            sys.stdout.write(rendered)
        return 0
    except (KmbFormatError, OSError, zipfile.BadZipFile, NotImplementedError, RuntimeError) as exc:
        print(json.dumps({
            "status": "error", "error_type": type(exc).__name__, "message": str(exc),
        }), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
