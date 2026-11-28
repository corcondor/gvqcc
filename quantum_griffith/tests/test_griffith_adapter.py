"""Compatibility tests for real upstream Griffith IR field conventions."""
import unittest

from quantum_griffith.griffith_adapter import (
    UnsupportedGriffithIR, from_griffith_ir, compile_griffith_ir
)
from quantum_griffith.reversible import verify_oracle


def make_doc(nodes, edges, in_width=2, out_width=2):
    return {
        "format": "magicdelta-ir", "version": "0.2.0", "metadata": {},
        "inputs": [{"id": "x", "width": in_width}],
        "outputs": [{"id": "y", "width": out_width}],
        "nodes": nodes,
        "edges": [{"src": a, "dst": b} for a, b in edges],
    }


class GriffithAdapterTests(unittest.TestCase):
    def test_two_serial_lut_layers_before_groupsum(self):
        nodes = [
            {"id": "l0", "type": "lut_layer", "params": {
                "in_width": 2, "out_width": 2, "n_inputs": 2,
                "indices": [[0, 0], [1, 1]],
                "truth_tables": ["0x6", "0x8"],  # XOR, AND
            }},
            {"id": "l1", "type": "lut_layer", "params": {
                "in_width": 2, "out_width": 2, "n_inputs": 2,
                "indices": [[0, 0], [1, 1]],
                "truth_tables": ["0x6", "0xe"],  # XOR, OR
            }},
            {"id": "sum", "type": "group_sum", "params": {
                "in_width": 2, "k": 2, "tau": 1.0
            }},
        ]
        doc = make_doc(
            nodes, [("x", "l0"), ("l0", "l1"), ("l1", "sum"), ("sum", "y")]
        )
        graph = from_griffith_ir(doc)
        for x in range(4):
            a, b = x & 1, (x >> 1) & 1
            xor, and_ = a ^ b, a & b
            self.assertEqual(graph.evaluate(x), (xor ^ and_, xor | and_))
        verify_oracle(compile_griffith_ir(doc), graph.truth_tables())

    def test_flat_irlowered_polarities_and_constants(self):
        doc = make_doc(
            [{"id": "flat", "type": "lut_flat", "params": {
                "in_width": 2, "out_width": 4,
                "gates": [[8, 1, 2]],  # AND input0,input1
                "outputs": [6, 7, 1, 0],  # AND, !AND, 1, 0
            }}],
            [("x", "flat"), ("flat", "y")], out_width=4,
        )
        graph = from_griffith_ir(doc)
        for x in range(4):
            and_ = (x & 1) & ((x >> 1) & 1)
            self.assertEqual(graph.evaluate(x), (and_, 1 ^ and_, 1, 0))
        verify_oracle(compile_griffith_ir(doc), graph.truth_tables())

    def test_unary_lut(self):
        doc = make_doc(
            [{"id": "l", "type": "lut_layer", "params": {
                "in_width": 1, "out_width": 1, "n_inputs": 1,
                "indices": [[0]], "truth_tables": ["0x1"],  # NOT
            }}],
            [("x", "l"), ("l", "y")], in_width=1, out_width=1
        )
        graph = from_griffith_ir(doc)
        self.assertEqual(graph.truth_tables(), ((1, 0),))
        verify_oracle(compile_griffith_ir(doc), graph.truth_tables())

    def test_reject_high_arity_lut_without_upstream_lowering(self):
        doc = make_doc(
            [{"id": "l", "type": "lut_layer", "params": {
                "in_width": 4, "out_width": 1, "n_inputs": 4,
                "indices": [[0], [1], [2], [3]],
                "truth_tables": ["0x8000"],
            }}], [("x", "l"), ("l", "y")], in_width=4, out_width=1
        )
        with self.assertRaises(UnsupportedGriffithIR):
            from_griffith_ir(doc)

    def test_reject_unresolved_binary_indices_sidecar(self):
        doc = make_doc(
            [{"id": "l", "type": "lut_layer", "params": {
                "in_width": 2, "out_width": 1, "n_inputs": 2,
                "indices": {"$data": "model.npz#indices"},
                "truth_tables": ["0x8"],
            }}], [("x", "l"), ("l", "y")], out_width=1
        )
        with self.assertRaises(UnsupportedGriffithIR):
            from_griffith_ir(doc)


if __name__ == "__main__":
    unittest.main()
