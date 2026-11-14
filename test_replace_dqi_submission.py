"""Packaging unit tests ONLY: tiny synthetic circuits and synthetic JSON records.

No fixture here is an actual DQI solution or a completed quantum verification.
The production baseline hash is patched within each test so the fixtures can
exercise ZIP preservation and rejection behavior without a 455 MB circuit.
"""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import replace_dqi_submission as pack


def synthetic_kmb(qubit):
    # A single X, encoded independently from the documented KMB v2 columns.
    magic = bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
    data = bytearray(struct.pack("<16s4I9Q", magic, 2, qubit + 1, 0, 0,
                                 1, 0, 0, 1, 0, 0, 0, 0, 0))
    for kind in range(1, 12):
        payload = b"\x11" if kind == 1 else struct.pack("<I", qubit) if kind == 7 else b"\0" * 8 if kind == 11 else b""
        data.extend(struct.pack("<QQ", kind, len(payload)) + payload)
    return bytes(data)


class ReplaceSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.baseline = self.root / "baseline.zip"
        self.candidate = self.root / "candidate.kmb"
        self.verification = self.root / "completed.json"
        self.output = self.root / "improved.zip"
        self.receipt = self.output.with_suffix(".receipt.json")
        self.old_dqi = synthetic_kmb(0)
        self.new_dqi = synthetic_kmb(1)
        self.candidate.write_bytes(self.new_dqi)
        self.record = {
            "_fixture_note": "SYNTHETIC PACKAGING TEST ONLY; no quantum verification was run",
            "status": "PASS", "verified_shots": 102400, "log2_delta": -128,
            "circuit_sha256": hashlib.sha256(self.new_dqi).hexdigest(),
            "num_qubits": 2, "num_bits": 0, "num_ops": 1,
            "value_errors": 0, "phase_errors": 0, "score": 123.0,
        }
        self.write_record()
        self.contents = {
            "invsqrt.kmx": b"unchanged custom inverse fixture\r\n\x00",
            "dfthcsos/": b"",
            "dfthcsos/submission.npz": b"user-specific refitted weights fixture\x00\xff",
            "dfthcsos/angle_k_0.kmb": b"user-specific angle-loader fixture\xff\0",
        }
        self.write_zip()
        self.pin = patch.object(pack, "BASELINE_DQI_SHA256", hashlib.sha256(self.old_dqi).hexdigest())
        self.pin.start()

    def tearDown(self):
        self.pin.stop()
        self.temp.cleanup()

    def write_record(self):
        self.verification.write_text(json.dumps(self.record), encoding="utf-8")

    def write_zip(self, extras=(), old_dqi=None, compression=zipfile.ZIP_DEFLATED):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.baseline, "w", compression=compression) as archive:
                archive.comment = b"baseline archive comment"
                archive.writestr("dqi.kmb", self.old_dqi if old_dqi is None else old_dqi)
                for name, payload in list(self.contents.items()) + list(extras):
                    archive.writestr(name, payload)

    def run_packager(self):
        return pack.replace_dqi(self.baseline, self.candidate, self.verification, self.output)

    def assert_rejected(self, error=pack.PackageError):
        baseline_before = self.baseline.read_bytes()
        with self.assertRaises(error):
            self.run_packager()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(self.baseline.read_bytes(), baseline_before)

    def test_every_non_dqi_payload_preserved_including_local_weights(self):
        original_archive = self.baseline.read_bytes()
        result = self.run_packager()
        self.assertEqual(self.baseline.read_bytes(), original_archive)
        self.assertEqual(self.candidate.read_bytes(), self.new_dqi)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.namelist(), ["dqi.kmb", *self.contents])
            self.assertEqual(archive.comment, b"baseline archive comment")
            self.assertEqual(archive.read("dqi.kmb"), self.new_dqi)
            for name, payload in self.contents.items():
                self.assertEqual(archive.read(name), payload)
        self.assertTrue(result["non_dqi_members_byte_identical"])
        self.assertEqual(result["preserved_file_count"], 3)
        self.assertEqual(result["output_archive"]["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        for member in result["members"]:
            if member["name"] != "dqi.kmb":
                self.assertEqual(member["before_sha256"], member["after_sha256"])
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt, result)
        self.assertEqual(receipt["verification"]["json_sha256"], hashlib.sha256(self.verification.read_bytes()).hexdigest())

    def test_streaming_crosses_chunk_boundaries_and_preserves_stored_member(self):
        payload = b"local factorization bytes\0\xff" * 95000
        self.contents["dfthcsos/submission.npz"] = payload
        self.write_zip(compression=zipfile.ZIP_STORED)
        self.run_packager()
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("dfthcsos/submission.npz"), payload)
            self.assertEqual(archive.getinfo("dfthcsos/submission.npz").compress_type, zipfile.ZIP_STORED)

    def test_wrong_baseline_dqi_is_rejected(self):
        self.write_zip(old_dqi=b"a different DQI")
        self.assert_rejected()

    def test_verification_hash_mismatch_is_rejected(self):
        self.record["circuit_sha256"] = "0" * 64
        self.write_record()
        self.assert_rejected()

    def test_failed_or_incomplete_verification_is_rejected(self):
        for key, value in (("status", "FAIL"), ("verified_shots", 256), ("num_shots", 256),
                           ("log2_delta", -8), ("log2_delta", None), ("num_qubits", 3),
                           ("num_ops", 2), ("value_errors", -1), ("score", 0)):
            with self.subTest(field=key, value=value):
                saved = self.record.copy()
                self.record[key] = value
                self.write_record()
                self.assert_rejected()
                self.record = saved

    def test_nonzero_errors_are_not_automatically_rejected_for_dqi(self):
        # DQI's real verifier permits some errors; the fixture tests only
        # that the packager does not invent an additional zero-error rule.
        self.record["value_errors"] = 1
        self.record["phase_errors"] = 2
        self.write_record()
        self.run_packager()
        self.assertTrue(self.output.exists())

    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        for text in ('{"status":"PASS","status":"FAIL"}', '{"score": NaN}'):
            self.verification.write_text(text)
            self.assert_rejected()

    def test_output_and_receipt_overwrites_are_rejected(self):
        for destination in (self.output, self.receipt):
            destination.write_bytes(b"existing result")
            with self.assertRaises(FileExistsError):
                self.run_packager()
            self.assertEqual(destination.read_bytes(), b"existing result")
            destination.unlink()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.receipt.exists())

    def test_input_output_alias_is_rejected(self):
        with self.assertRaises(pack.PackageError):
            pack.replace_dqi(self.baseline, self.candidate, self.verification, self.baseline)

    def test_duplicate_and_case_ambiguous_zip_members_are_rejected(self):
        for extra in ("dqi.kmb", "invsqrt.kmx", "INVSQRT.KMX"):
            with self.subTest(extra=extra):
                self.write_zip(extras=((extra, b"duplicate"),))
                self.assert_rejected()

    def test_path_traversal_absolute_and_windows_paths_are_rejected(self):
        for name in ("../bad", "/bad", "C:/bad", "folder\\bad", "folder/../bad", "folder//bad", "folder/./bad"):
            with self.subTest(name=name):
                self.write_zip(extras=((name, b"unsafe path fixture"),))
                self.assert_rejected()

    def test_ambiguous_dqi_extensions_and_locations_are_rejected(self):
        for name in ("dqi.kmx", "DQI.KMB", "nested/dqi.kmb", "dqi.kmb.xz", "dqi.txt", "dqi/"):
            with self.subTest(name=name):
                self.write_zip(extras=((name, b""),))
                self.assert_rejected()

    def test_file_directory_shadowing_is_rejected(self):
        self.write_zip(extras=(("file", b"regular"), ("file/child", b"child")))
        self.assert_rejected()

    def test_symlink_member_is_rejected(self):
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.baseline, "a") as archive:
            archive.writestr(info, "../outside")
        self.assert_rejected()

    def test_invalid_candidate_kmb_is_rejected(self):
        self.candidate.write_bytes(b"not KMB")
        self.record["circuit_sha256"] = hashlib.sha256(self.candidate.read_bytes()).hexdigest()
        self.write_record()
        self.assert_rejected(ValueError)

    def test_cli_reports_rejection_without_creating_output(self):
        self.record["verified_shots"] = 256
        self.write_record()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = pack.main([str(self.baseline), str(self.candidate), str(self.verification), str(self.output)])
        self.assertEqual(code, 1)
        self.assertIn("102400", stderr.getvalue())
        self.assertFalse(self.output.exists())

    def test_named_flags_used_by_reproduction_driver(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = pack.main(["--baseline-zip", str(self.baseline), "--dqi", str(self.candidate),
                              "--verification", str(self.verification), "--output", str(self.output)])
        self.assertEqual(code, 0)
        self.assertTrue(self.output.exists())
        self.assertEqual(json.loads(stdout.getvalue())["dqi_sha256"], self.record["circuit_sha256"])


if __name__ == "__main__":
    unittest.main()
