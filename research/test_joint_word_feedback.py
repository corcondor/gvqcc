"""Tests for coupled word transitions and algebraic screen (no KickMix needed)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from joint_word_feedback import (batch_delta, gf2_rank, rank_effect, rank_profile,
                                 affected_slots, physical_pass)


class CoupledWordFeedbackTests(unittest.TestCase):
    def test_rank_gf2_not_real_rank(self):
        matrix = np.array([[1, 0, 1], [0, 1, 1], [1, 1, 0]], dtype=np.uint8)
        self.assertEqual(gf2_rank(matrix), 2)
        self.assertEqual(gf2_rank(np.zeros((4, 17), dtype=np.uint8)), 0)

    def test_word_changes_two_adjacent_slots(self):
        words = np.random.default_rng(20261123).integers(0, 128, size=(32, 15))
        before = [batch_delta(words, k) for k in range(3)]
        row, col = 19, 6  # k=1; word index inside the batch=1
        words[row, col] ^= 1
        after = [batch_delta(words, k) for k in range(3)]
        self.assertEqual(affected_slots(col, 15), (1, 2))
        self.assertTrue(np.array_equal(before[0], after[0]))
        self.assertEqual(int((before[1] ^ after[1]).sum()), 1)
        self.assertEqual(int((before[2] ^ after[2]).sum()), 1)
        self.assertEqual(int((before[1] ^ after[1])[row, 1]), 1)
        self.assertEqual(int((before[2] ^ after[2])[row, 1]), 1)

    def test_rank_change_matches_full_recompute(self):
        rng = np.random.default_rng(8)
        words = rng.integers(0, 128, size=(48, 15))
        baseline = rank_profile(words)
        dr = rank_effect(words, 27, 6, baseline)
        words[27, 6] ^= 1
        self.assertEqual(dr, sum(rank_profile(words)) - sum(baseline))

    def test_physics_strict_floor(self):
        m = dict(error_1=.019, error_2=.019, Lambda=51.0, E_gap=3.914898001,
                 gap_in_domain=True, lambda_eff=46.9)
        self.assertTrue(physical_pass(m))
        m['E_gap'] = 3.914898
        self.assertFalse(physical_pass(m))
        m['E_gap'] = 3.914898001
        m['error_2'] = .020000001
        self.assertFalse(physical_pass(m))


if __name__ == '__main__':
    unittest.main()
