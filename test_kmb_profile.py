"""Small format/streaming regression checks; no competition files are needed."""

import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

import kmb_profile as kp


HERE = Path(__file__).resolve().parent
FIXTURES = json.loads((HERE / "kmb_official_fixtures.json").read_text())["examples"]


def official(index):
    return bytes.fromhex(FIXTURES[index]["hex"])


def packet_locations(data):
    header = kp.HEADER.unpack(data[:kp.HEADER.size])
    offset = kp.HEADER.size
    packets = []
    for _ in range(header[4] + 11):
        kind, length = kp.PACKET.unpack_from(data, offset)
        packets.append((kind, offset, offset + 16, length))
        offset += 16 + length
    return packets


def write_repeated_ccx(path, n_ops, block_bytes=65536):
    """Generate a large synthetic test without materializing its operations."""
    def repeat(output, value, count):
        chunk_count = max(1, block_bytes // len(value))
        block = value * chunk_count
        while count:
            take = min(count, chunk_count)
            output.write(block[:take * len(value)])
            count -= take

    with Path(path).open("wb") as output:
        output.write(kp.HEADER.pack(
            kp.MAGIC, 2, 3 if n_ops else 0, 0, 0,
            n_ops, n_ops, 0, 0, 0, 0, 0, 0, 0,
        ))
        for kind in range(1, 12):
            size = n_ops if kind == 1 else 4 * n_ops if kind in (2, 3, 4) else 8 if kind == 11 else 0
            output.write(kp.PACKET.pack(kind, size))
            if kind == 1:
                repeat(output, b"\x31", n_ops)
            elif kind in (2, 3, 4):
                repeat(output, struct.pack("<I", kind - 2), n_ops)
            elif kind == 11:
                output.write(struct.pack("<Q", 0))


class KmbProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def check_bytes(self, data, **kwargs):
        path = self.root / "input.kmb"
        path.write_bytes(data)
        return kp.profile(path, chunk_bytes=4096, **kwargs)

    def reject(self, data):
        with self.assertRaises(kp.KmbFormatError):
            self.check_bytes(data)

    def test_four_official_hex_dumps(self):
        expected = [(0, 0, 0), (3, 3, 1), (147, 16, 16), (43, 25, 2)]
        for index, (ops, qubits, ccx) in enumerate(expected):
            with self.subTest(fixture=FIXTURES[index]["name"]):
                data = official(index)
                result = self.check_bytes(data)
                self.assertEqual(result["header"]["num_ops"], ops)
                self.assertEqual(result["header"]["num_qubits"], qubits)
                self.assertEqual(result["raw_gate_families"]["CCX"]["total"], ccx)
                self.assertEqual(result["raw_kmb_sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(result["validation"]["binary_layout"], "passed")
                self.assertEqual(
                    result["storage"]["header_bytes"] + result["storage"]["packet_bytes_total"],
                    len(data),
                )

    def test_conditional_counts_and_register_aliases(self):
        result = self.check_bytes(official(3))
        self.assertEqual(result["raw_gate_families"]["CCX"], {
            "without_explicit_condition": 1, "with_explicit_condition": 1, "total": 2,
        })
        self.assertEqual(result["registers"]["summaries"][0]["first_targets"], ["q0", "b0"])
        self.assertEqual(result["header"]["num_ops_with_angle"], 2)
        self.assertEqual(result["header"]["num_info_tags"], 1)

    def test_register_output_cap(self):
        result = self.check_bytes(official(3), max_register_summaries=1)
        self.assertEqual(len(result["registers"]["summaries"]), 1)
        self.assertEqual(result["registers"]["summaries_omitted"], 1)
        self.assertEqual(result["header"]["num_bits"], 26)

    def test_zip_stored_and_deflated(self):
        for compression in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            with self.subTest(compression=compression):
                path = self.root / f"submission_{compression}.zip"
                with zipfile.ZipFile(path, "w", compression=compression) as archive:
                    archive.writestr("nested/dqi.kmb", official(2))
                    archive.writestr("irrelevant.txt", "ignored")
                result = kp.profile(path, chunk_bytes=4096)
                self.assertEqual(result["source"]["member"], "nested/dqi.kmb")
                self.assertEqual(result["raw_gate_families"]["CCX"]["total"], 16)
                explicit = kp.profile(path, "nested/dqi.kmb", chunk_bytes=4096)
                self.assertEqual(result["raw_kmb_sha256"], explicit["raw_kmb_sha256"])

    def test_ambiguous_and_missing_zip_members(self):
        path = self.root / "ambiguous.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("first.kmb", official(0))
            archive.writestr("second.kmb", official(0))
        with self.assertRaises(kp.KmbFormatError):
            kp.profile(path)
        with self.assertRaises(kp.KmbFormatError):
            kp.profile(path, "missing.kmb")
        self.assertEqual(kp.profile(path, "first.kmb")["header"]["num_ops"], 0)

    def test_duplicate_zip_member_names(self):
        import warnings
        path = self.root / "duplicate.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("dqi.kmb", official(0))
                archive.writestr("dqi.kmb", official(0))
        with self.assertRaises(kp.KmbFormatError):
            kp.profile(path, "dqi.kmb")

    def test_zip_crc_is_checked(self):
        path = self.root / "bad_crc.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("dqi.kmb", official(0))
        raw = bytearray(path.read_bytes())
        start = raw.index(kp.MAGIC)
        raw[start] ^= 1
        path.write_bytes(raw)
        with self.assertRaises((zipfile.BadZipFile, kp.KmbFormatError)):
            kp.profile(path)

    def test_wrong_magic(self):
        data = bytearray(official(0))
        data[0] ^= 1
        self.reject(data)

    def test_wrong_version(self):
        data = bytearray(official(0))
        struct.pack_into("<I", data, 16, 3)
        self.reject(data)

    def test_truncated_headers_and_payloads(self):
        data = official(3)
        for length in (0, 15, 103, 104, 105, 119, len(data)-1):
            with self.subTest(length=length):
                self.reject(data[:length])

    def test_trailing_bytes(self):
        self.reject(official(0) + b"\x00")

    def test_packet_order(self):
        data = bytearray(official(0))
        struct.pack_into("<Q", data, kp.HEADER.size, 2)
        self.reject(data)

    def test_packet_length(self):
        data = bytearray(official(0))
        struct.pack_into("<Q", data, kp.HEADER.size + 8, 1)
        self.reject(data)

    def test_inconsistent_header_counts(self):
        data = bytearray(official(1))
        # Keep all packet sizes unchanged; replace the single X by a no-target NEG.
        p = next(p for p in packet_locations(data) if p[0] == 1)
        data[p[2] + 2] = 0
        self.reject(data)

    def test_impossible_header_count(self):
        data = bytearray(official(0))
        struct.pack_into("<Q", data, 32, 2**63)
        self.reject(data)

    def test_unknown_operation(self):
        data = bytearray(official(1))
        p = next(p for p in packet_locations(data) if p[0] == 1)
        data[p[2]] = 0xFF
        self.reject(data)

    def test_maximum_ids_exact_and_bounded(self):
        for offset, value in ((20, 4), (20, 2), (20, 500_000_001), (24, 1)):
            with self.subTest(offset=offset, value=value):
                data = bytearray(official(1))
                struct.pack_into("<I", data, offset, value)
                self.reject(data)

    def test_duplicate_two_and_three_qubit_targets(self):
        for first_kind, second_kind in ((2, 3), (2, 4), (3, 4), (5, 6)):
            with self.subTest(pair=(first_kind, second_kind)):
                data = bytearray(official(1))
                packets = {p[0]: p for p in packet_locations(data)}
                first = packets[first_kind][2]
                second = packets[second_kind][2]
                data[second:second+4] = data[first:first+4]
                self.reject(data)

    def test_info_tag_count_and_offset(self):
        for displacement, value in ((0, 0), (8, 3), (8, 5)):
            with self.subTest(displacement=displacement, value=value):
                data = bytearray(official(3))
                p = next(p for p in packet_locations(data) if p[0] == 11)
                struct.pack_into("<Q", data, p[2] + displacement, value)
                self.reject(data)

    def test_register_payload_lengths(self):
        data = bytearray(official(1))
        p = packet_locations(data)[0]
        struct.pack_into("<I", data, p[2], 2000)
        self.reject(data)

    def test_short_reads_are_supported(self):
        class ShortReader(io.BytesIO):
            def read(self, n=-1):
                if n < 0 or n > 4096:
                    raise AssertionError("Unbounded or oversize read")
                return super().read(min(n, 7))
        data = official(3)
        result, _ = kp.scan_stream(ShortReader(data), len(data), 4096, 128)
        self.assertEqual(result["header"]["num_ops"], 43)

    def test_synthetic_stream_crosses_chunk_boundaries(self):
        path = self.root / "stream.kmb"
        write_repeated_ccx(path, 10003)
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        result = kp.profile(path, chunk_bytes=4099)
        self.assertEqual(result["raw_gate_families"]["CCX"]["total"], 10003)
        self.assertEqual(
            result["validation"]["disjoint_gate_targets"]["three_qubit_operations"], 10003,
        )
        self.assertEqual(result["raw_kmb_sha256"], before)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_cli_does_not_overwrite_input_or_existing_output(self):
        from contextlib import redirect_stderr
        source = self.root / "source.kmb"
        source.write_bytes(official(0))
        output = self.root / "output.json"
        output.write_text("keep existing result")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(kp.main([str(source), "--output", str(source)]), 2)
            self.assertEqual(kp.main([str(source), "--output", str(output)]), 2)
        self.assertEqual(source.read_bytes(), official(0))
        self.assertEqual(output.read_text(), "keep existing result")


if __name__ == "__main__":
    unittest.main()
