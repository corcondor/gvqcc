"""Deterministic packaging and score tests; not an official verifier run."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import frontier_dqi_exact_trial as trial


def digest(b):
    return hashlib.sha256(b).hexdigest()


def mock_archive(path, dqi=b"original"):
    contents = {"invsqrt.kmb": b"inverse", "dqi.kmb": dqi,
                "dfthcsos/submission.npz": b"chem"}
    contents.update({f"dfthcsos/angle_k_{i}.kmb": bytes([i]) for i in range(15)})
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for name, value in contents.items():
            z.writestr(name, value)
    return contents


class FrontierExactTrialTests(unittest.TestCase):
    def test_gm_monotonic(self):
        a = trial.gm(75006.3765, 347375470571.73, 294762732.98)
        b = trial.gm(75006.3765, 347000000000.0, 294762732.98)
        self.assertGreater(b, a)
        self.assertAlmostEqual(a, 28.0948717, places=5)

    def test_pinned_archive_and_exact_17_member_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "base.zip"
            members = mock_archive(original)
            with patch.object(trial, "INVSQRT_SHA", digest(members["invsqrt.kmb"])), \
                 patch.dict(trial.DQI_COST, {digest(members["dqi.kmb"]): 123.0}, clear=True), \
                 patch.dict(trial.CHEM_COST, {digest(members["dfthcsos/submission.npz"]): 456.0}, clear=True):
                receipt = trial.extract_baseline(original, root / "dqi.kmb")
            self.assertEqual(receipt["member_count"], 18)
            self.assertEqual(receipt["dqi_reference_cost"], 123.0)
            candidate = root / "new.kmb"
            candidate.write_bytes(b"new-dqi")
            output = root / "new.zip"
            trial.repack(original, candidate, output)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(set(z.namelist()), trial.MEMBERS)
                for name, data in members.items():
                    self.assertEqual(z.read(name), b"new-dqi" if name == "dqi.kmb" else data)

    def test_reject_unrecognized_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "base.zip"
            mock_archive(original)
            with self.assertRaises(ValueError):
                trial.extract_baseline(original, root / "dqi.kmb")

    def test_reject_extra_member(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "base.zip"
            mock_archive(original)
            with zipfile.ZipFile(original, "a") as z:
                z.writestr("extra.txt", b"unexpected")
            with self.assertRaises(ValueError):
                trial.extract_baseline(original, root / "dqi.kmb")


if __name__ == "__main__":
    unittest.main()
