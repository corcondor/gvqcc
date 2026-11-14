"""Independent truth-table checks of affine-basis quadratic rank accounting."""
import random
import unittest

import dqi_affine_ccx_scan as scan


def simulate(ops, state, active_ccx=None):
    values = [(state >> i) & 1 for i in range(6)]
    ccx = 0
    for op in ops:
        q = op.qubits
        if op.opcode == 0x11:
            values[q[0]] ^= 1
        elif op.opcode == 0x21:
            values[q[1]] ^= values[q[0]]
        elif op.opcode == 0x22:
            values[q[0]], values[q[1]] = values[q[1]], values[q[0]]
        elif op.opcode == 0x31:
            if active_ccx is None or ccx in active_ccx:
                values[q[2]] ^= values[q[0]] & values[q[1]]
            ccx += 1
    return sum(v << i for i, v in enumerate(values))


def truth_to_anf(table):
    coefficients = list(table)
    for i in range(6):
        for mask in range(64):
            if mask & (1 << i):
                coefficients[mask] ^= coefficients[mask ^ (1 << i)]
    return {m for m, v in enumerate(coefficients) if v}


class AffineScanTests(unittest.TestCase):
    def test_rank_and_shared_products_against_independent_truth_tables(self):
        rng = random.Random(20261115)
        O = scan.shared.Operation
        checked = 0
        for trial in range(64):
            # Every physical wire is included, so the scanner's sorted index
            # coincides with the independently enumerated input bit index.
            ops = [O(0x11, (i,)) for i in range(6)]
            for j in range(28):
                kind = rng.randrange(4)
                if kind == 0:
                    a, b = rng.sample(range(3), 2)
                    ops.append(O(0x31, (a, b, rng.randrange(3, 6))))
                elif kind == 1:
                    bank = range(3) if rng.randrange(2) else range(3, 6)
                    ops.append(O(0x21, tuple(rng.sample(list(bank), 2))))
                elif kind == 2:
                    bank = range(3) if rng.randrange(2) else range(3, 6)
                    ops.append(O(0x22, tuple(rng.sample(list(bank), 2))))
                else:
                    ops.append(O(0x11, (rng.randrange(6),)))
            result = scan.inspect_piece(ops)
            self.assertNotIn('split_before', result)
            baseline = [simulate(ops, x, set()) for x in range(64)]
            for group in result['output_groups']:
                difference = [simulate(ops, x, set(group['ids'])) ^ baseline[x] for x in range(64)]
                values = {v for v in difference if v}
                self.assertLessEqual(len(values), 1)
                if values:
                    v = next(iter(values))
                    p = truth_to_anf([int(z == v) for z in difference])
                else:
                    p = set()
                self.assertEqual(scan.quadratic_rank(p, 6), group['polar_rank'])
                checked += 1
            for group in result['input_groups']:
                quadratics = []
                for i in group['ids']:
                    difference = [simulate(ops, x, {i}) ^ baseline[x] for x in range(64)]
                    values = {v for v in difference if v}
                    self.assertLessEqual(len(values), 1)
                    if values:
                        v = next(iter(values))
                        p = truth_to_anf([int(z == v) for z in difference])
                    else:
                        p = set()
                    quadratics.append({m for m in p if m.bit_count() == 2})
                self.assertTrue(all(p == quadratics[0] for p in quadratics))
                checked += 1
        self.assertGreater(checked, 100)
        print('independent_groups_checked', checked, 'input_assignments_per_table', 64)

    def test_constructed_cases_and_nonlinear_control_barrier(self):
        self.assertEqual(scan.self_check()['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
