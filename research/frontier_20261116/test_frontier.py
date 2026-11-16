"""Small deterministic tests; not official quantum circuit verification."""
import base64
import json
import math
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile
import zlib

import numpy as np
import frontier_score_gate as cost
import frontier_hybrid_builder as hybrid
import rank43_42_joint_gpu as gpu


class CostAndProjection(unittest.TestCase):
    def test_28_09_gm(self):
        self.assertAlmostEqual(cost.gm(cost.PUBLIC_28_09), 28.09487171868039, places=7)

    def test_smaller_c_model_only(self):
        x = cost.c_scenarios({**cost.PUBLIC_28_09, "dqi": cost.OUR_VERIFIED_LOCAL["dqi"]})
        self.assertEqual([a["C"] for a in x["rows"]], [44, 43, 42])
        self.assertTrue(all(a["status"] == "COST_ONLY_NOT_VERIFIED" for a in x["rows"]))
        self.assertLess(x["rows"][1]["score_if_numeric_and_native_pass"], 28.3)

    def test_dqi_q_trade(self):
        a = cost.dqi_qubit_tradeoff(890, 368137.84857421875, q_new=880)
        self.assertGreater(a["extra_T_budget"], 8000)
        b = cost.dqi_qubit_tradeoff(890, 368137.84857421875, r_ratio=1.10, q_new=880)
        self.assertLess(b["extra_T_budget"], a["extra_T_budget"])

    def test_c43_native_coordinates(self):
        rng = np.random.default_rng(172)
        w = rng.normal(size=(2, 5, 3))
        ii = rng.normal(size=(2, 3))
        g = np.zeros((2, 2, 5, 5))
        for r in range(2): g[r, r] = np.eye(5)
        base = {"W": w, "H2_I": ii}
        lower, d = gpu.compressed_start(base, g, 2, 1)
        can = gpu.as_candidate(base, lower, d)
        np.testing.assert_allclose(can["H2_I"] - can["W"].sum(1), d)
        self.assertEqual(can["W"].shape, (2, 5, 2))

    def test_reject_numerical_threshold(self):
        x = {"error_1": .019, "error_2": .019, "Lambda": 250,
             "E_gap": 3.92, "lambda_eff": 46}
        self.assertTrue(gpu.passes(x))
        self.assertFalse(gpu.passes({**x, "error_2": .0200001}))


class PublicRawNotebook(unittest.TestCase):
    @staticmethod
    def raw_note(binary):
        inv = base64.b64encode(zlib.compress(binary)).decode()
        pins = {"dqi.kmb": ("1"*64, 11),
                "dfthcsos/submission.npz": ("2"*64, 12)}
        pins.update({f"dfthcsos/angle_k_{i}.kmb": ("3"*64, 13) for i in range(15)})
        notebook = {"cells": [
            {"cell_type":"code", "source": "PINNED = " + repr(pins)},
            {"cell_type":"code", "source": "INV = " + repr(inv)}]}
        return json.dumps({"blob":{"source":json.dumps(notebook)}}).encode()

    def test_parse_without_execution(self):
        payload = b"NOT-A-REAL-KMB-BUT-HASHED"
        with patch.object(hybrid, "EXPECTED_INVSQRT", hybrid.sha(payload)):
            pins, got = hybrid.decode_notebook(self.raw_note(payload))
        self.assertEqual(len(pins), 17)
        self.assertEqual(got, payload)

    def test_fails_if_wrong_hash(self):
        with self.assertRaises(ValueError):
            hybrid.decode_notebook(self.raw_note(b"wrong"))

    def test_exec_not_allowed(self):
        with self.assertRaises((ValueError, SyntaxError)):
            hybrid.literal_assignment("PINNED = __import__('os').system('echo bad')", "PINNED")


if __name__ == "__main__":
    unittest.main()
