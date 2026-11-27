#!/usr/bin/env python3
"""Emit the complete even-word infinity-CF codec, with coherent branch guards.

This is a codec, NOT a DQI phase oracle and NOT a repaired 316k submission.
There is no external choice of branch: all (i,d) stages are emitted and the
quantum data computes each guard. The straightforward controlled construction
is expensive. At 70 words it has 630 potential stages; no cost advantage is
claimed. KMX output is streamed to avoid retaining the entire expanded tape.

Requires the separately pinned V127 infinity-CF sources and the public kit.
No circuit from either source directory is overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import os
import sys
import tempfile


class Emitter:
    def __init__(self, source: Path, kit: Path, words: int):
        if words < 2 or words % 2:
            raise ValueError('word count must be positive and even')
        os.environ['DQI_KIT'] = str(kit.resolve())
        sys.path.insert(0, str(source.resolve()))
        self.km = importlib.import_module('kickmix')
        self.inv = importlib.import_module('native_dyadic')
        self.boundary = importlib.import_module('boundary_counter')
        self.ref = importlib.import_module('infinity_cf')
        self.words = words
        self.data = words * 12
        self.flag = self.data
        self.anc = self.data + 1
        self._temp = tempfile.TemporaryDirectory(prefix='coherent-codec-')
        self._cache = {}

    def tape(self, kind, *args):
        key = (kind, args)
        if key in self._cache:
            return self._cache[key]
        circuit = (self.inv.build(*args)[0] if kind == 'inverse'
                   else self.boundary.build(*args, n=self.words))
        path = Path(self._temp.name) / ('_'.join(map(str, (kind, *args))) + '.kmx')
        circuit.to_file(str(path), format='kmx')
        counts = Counter()
        # Stream on subsequent uses; do not retain millions of gate tuples.
        with path.open() as stream:
            for line in stream:
                fields = line.split()
                if not fields or fields[0] in ('REGISTER', 'APPEND_TO_REGISTER', 'INFO_TAG'):
                    continue
                if fields[0] not in ('X', 'CX', 'CCX', 'SWAP', 'CSWAP'):
                    raise ValueError(f'Non-unitary/unsupported tape operation: {fields!r}')
                if any(not x.startswith('q') for x in fields[1:]):
                    raise ValueError(f'Unexpected classical condition: {fields!r}')
                counts[fields[0]] += 1
        value = path, circuit.num_qubits, counts
        self._cache[key] = value
        return value

    @staticmethod
    def gates(path):
        with path.open() as stream:
            for line in stream:
                fields = line.split()
                if fields and fields[0] in ('X', 'CX', 'CCX', 'SWAP', 'CSWAP'):
                    yield fields[0], [int(q[1:]) for q in fields[1:]]

    def emit(self, output: Path, reverse=False):
        output = output.resolve()
        if output.exists():
            raise FileExistsError(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        schedule = [(i, d) for i in range(0, self.words, 2)
                    for d in range(1, (self.words-i)//2+1)]
        if reverse:
            schedule.reverse()
        stats = Counter()
        peak = self.data + 1
        with output.open('x') as out:
            for j in range(self.words):
                out.write(f'REGISTER r{j} "S{j}"\n')
                for k in range(12):
                    out.write(f'APPEND_TO_REGISTER q{12*j+k} r{j}\n')

            def write(op, *qs):
                out.write(op + ''.join(f' q{q}' for q in qs) + '\n')
                stats[op] += 1

            for stage, (i, d) in enumerate(schedule):
                p = i+d-1
                length = self.words-p
                guard_path, guard_width, _ = self.tape('guard', i, d)
                inverse_path, inverse_width, _ = self.tape('inverse', length)
                tmp = self.anc + inverse_width - 12*length
                peak = max(peak, guard_width, tmp+1)

                def guard():
                    # Guard has all input data, then one XOR output, then clean
                    # scratch; these match this emitter's physical layout.
                    for op, qs in self.gates(guard_path):
                        write(op, *qs)

                def wire(q):
                    return 12*p+q if q < 12*length else self.anc+q-12*length

                guard()
                for op, qs in self.gates(inverse_path):
                    z = [wire(q) for q in qs]
                    if op == 'X':
                        write('CX', self.flag, z[0])
                    elif op == 'CX':
                        write('CCX', self.flag, *z)
                    elif op == 'SWAP':
                        write('CSWAP', self.flag, *z)
                    else:
                        write('CCX', self.flag, z[0], tmp)
                        write(op, tmp, z[1], z[2])
                        write('CCX', self.flag, z[0], tmp)
                # Prefix zeros / first-nonzero status are invariant under this
                # reciprocal, so exactly the same guard erases its output.
                guard()
                if stage % 25 == 0:
                    print(json.dumps({'stage': stage, 'stages': len(schedule),
                                      'i': i, 'd': d, 'ops': sum(stats.values())}), flush=True)
        result = {'words': self.words, 'stages': len(schedule), 'reverse': reverse,
                  'ops': sum(stats.values()), 'static_paid':
                  sum(stats[k] for k in ('CCX', 'CCZ', 'CSWAP')),
                  'max_referenced_qubits_bound': peak,
                  'bytes': output.stat().st_size,
                  'sha256': hashlib.file_digest(output.open('rb'), 'sha256').hexdigest(),
                  'scope': 'complete coherent codec tape; not DQI phase oracle',
                  'submission_performed': False}
        return result


def check(emitter, forward, backward):
    import numpy as np
    km, n, ref = emitter.km, emitter.words, emitter.ref
    rng = np.random.default_rng(20261128)
    rows = []
    for z in range(n+1):
        for _ in range(4):
            r = rng.integers(0, 4096, n, dtype=np.int64)
            r[:z] = 0
            rows.append(r)
    for w in range(n//2+1):
        for _ in range(8):
            xs = rng.choice(np.arange(1, 4096), w, replace=False)
            errors = {int(x): int(v) for x, v in zip(xs, rng.integers(1, 4096, w))}
            rows.append(ref.D.moments(errors, n))
    rows = np.asarray(rows, dtype=np.int64)
    encoded = np.asarray([ref.encode(r) for r in rows], dtype=np.int64)

    def bits(x):
        return ((x[:, :, None] >> np.arange(12)) & 1).reshape(len(x), -1).T.astype(bool)

    inputs, outputs = bits(rows), bits(encoded)
    errors = [0, 0, 0]
    shots = 0
    for path, src, target in [(forward, inputs, outputs), (backward, outputs, inputs)]:
        circuit = km.Circuit.from_file(str(path), format='kmx')
        data = km.array([km.q(j) for j in range(12*n)])
        anc = km.array([km.q(j) for j in range(12*n, circuit.num_qubits)])
        for seed in (12701, 12702):
            for st in range(0, len(rows), 64):
                en = min(st+64, len(rows))
                sim = km.Simulator(batch_size=en-st, seed=seed, debug_print=False)
                sim.use_same_registers_as(circuit)
                sim.write_across_shots(data, src[:, st:en])
                sim.do(circuit)
                errors[0] += int((sim.read_across_shots(data) ^ target[:, st:en]).any(0).sum())
                errors[1] += int(sim.read_across_shots(anc).any(0).sum())
                errors[2] += int(sim.read_phase_flipped_across_shots().sum())
                shots += en-st
    result = {'native_shots': shots, 'value_dirty_phase_errors': errors,
              'test_words': n, 'scope': 'codec reference comparison; not oracle proof'}
    if any(errors):
        raise AssertionError(result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--kit', type=Path, required=True)
    p.add_argument('--words', type=int, default=70)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    emitter = Emitter(a.source, a.kit, a.words)
    out = a.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    forward = out / f'coherent_{a.words}_forward.kmx'
    backward = out / f'coherent_{a.words}_reverse.kmx'
    result = {'forward': emitter.emit(forward), 'reverse': emitter.emit(backward, True)}
    if a.check:
        result['native_check'] = check(emitter, forward, backward)
    (out/'receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
