"""Ensure binary splicing retains every operand column and refuses bad boundaries."""
import json
from pathlib import Path
import tempfile
import unittest

import kmb_splice as splice
import dqi_ccx_peephole as pp
from test_dqi_ccx_peephole import fixture_bytes, op


class SpliceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.readers = []
        self.registers = [('S0', [0x80000000, 0x80000001]), ('E0', [0])]

    def tearDown(self):
        for reader in self.readers:
            reader.close()
        self.tmp.cleanup()

    def circuit(self, name, operations, registers=None):
        path = self.root / name
        path.write_bytes(fixture_bytes(operations, self.registers if registers is None else registers))
        reader = splice.open_circuit(path)
        self.readers.append(reader)
        return reader

    def test_identity_splice_retains_all_ten_columns(self):
        operations = [op(1, condition=2), op(0x31, 0, 1, 2, condition=3),
                      op(0x21, 2, 3), pp.Operation(0x13, (3,), None, None, bytes(range(16))),
                      op(0x50, 3, bit=5), op(0x40, bit=5), op(1)]
        circuit = self.circuit('all.kmb', operations)
        out = self.root / 'identity.kmb'
        splice.write_segments(out, circuit, [(circuit, 0, 2), (circuit, 2, 5), (circuit, 5, 7)])
        self.assertEqual(out.read_bytes(), (self.root / 'all.kmb').read_bytes())

    def test_changed_prefix_preserves_body_and_suffix(self):
        before = self.circuit('before.kmb', [op(0x40, bit=0), op(0x31, 0, 1, 2), op(0x50, 2, bit=3)])
        prefix = self.circuit('prefix.kmb', [op(0x41, bit=7), op(0x42, bit=7)])
        out = self.root / 'combined.kmb'
        report = splice.write_segments(out, before, [(prefix, 0, 2), (before, 1, 3)])
        combined = splice.open_circuit(out)
        self.readers.append(combined)
        self.assertEqual(report['header']['num_bits'], 8)
        self.assertTrue(splice.compare_ranges(before, 1, 3, combined, 2, 4)['equal'])
        self.assertFalse(splice.compare_ranges(before, 0, 1, prefix, 0, 1)['equal'])
        self.assertFalse(splice.compare_ranges(before, 0, 1, prefix, 0, 2)['equal'])

    def test_register_mismatch_and_overwrite_refused(self):
        before = self.circuit('source.kmb', [op(0x11, 0)])
        wrong = self.circuit('wrong.kmb', [op(0x11, 0)], [('different', [0x80000000])])
        with self.assertRaisesRegex(ValueError, 'Register'):
            splice.write_segments(self.root / 'bad.kmb', before, [(wrong, 0, 1)])
        with self.assertRaises(FileExistsError):
            splice.write_segments(self.root / 'source.kmb', before, [(before, 0, 1)])
        with self.assertRaisesRegex(ValueError, 'Invalid operation range'):
            splice.write_segments(self.root / 'range.kmb', before, [(before, -1, 1)])

    def test_cached_profile_must_match_input_hash(self):
        before = self.circuit('source.kmb', [op(0x11, 0)])
        profile = dict(before.profile, raw_kmb_sha256='0' * 64)
        cache = self.root / 'wrong.json'
        cache.write_text(json.dumps(profile))
        with self.assertRaisesRegex(ValueError, 'different circuit'):
            splice.open_circuit(self.root / 'source.kmb', cache)


if __name__ == '__main__':
    unittest.main()
