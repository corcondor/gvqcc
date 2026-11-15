#!/usr/bin/env python3
"""Bind selected late DQI width peaks to unmodified source components.

Read-only whole-tape audit. Small templates and a receipt are written only to
the requested output directory; no production KMB is modified or simulated.
The exact opcode/operand match is invariant under injective wire renaming.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent / 'official_sources/Syed_v12/source/dqi_source/src/controller_work'
for relative in ('after_c5/converter_width', 'night_c27/arithmetic',
                 'after_c5/extractor_width', 'after_c5/arithmetic_t'):
    sys.path.insert(0, str(WORK / relative))
import cw_paths  # noqa: E402,F401
import kickmix as km  # noqa: E402
import gauge_park_paired as Paired  # noqa: E402
import gauge_park_lender as Lender  # noqa: E402
import gf24_arithmetic as GF24  # noqa: E402
import direct_carry_arithmetic as Direct  # noqa: E402
import dual_scale as Dual  # noqa: E402
import kmb_splice as Splice  # noqa: E402
from outcome_dqi_chart_match import match  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def wire_ids(word):
    return [int(str(q)[1:]) for q in word]


def build(label, directory):
    b = km.CircuitBuilder()
    roles = {}
    if label == 'paired_divide_prefix':
        factor = b.create_quantum_register(12, 'factor')
        words = [b.create_quantum_register(12, 'target_a'),
                 b.create_quantum_register(12, 'target_b')]
        flag = b.create_quantum_register(1, 'gauge_flag')
        loan = Lender.GaugeLender(b, flag[0])
        inverse_mask = Paired.divide_prefix(loan, words, factor)
        roles.update(factor=wire_ids(factor), target_a=wire_ids(words[0]),
                     target_b=wire_ids(words[1]), inverse_mask=wire_ids(inverse_mask))
    elif label == 'scalar_consume_closed':
        word, factor, inverse = [b.create_quantum_register(12, n)
                                for n in ('word', 'factor', 'inverse')]
        temporary = b.alloc_qubits(12)
        Dual.scale_word(b, word, inverse, factor, temporary)
        b.free(temporary)
        roles.update(word=wire_ids(word), factor=wire_ids(factor), inverse=wire_ids(inverse))
    elif label in ('product24_consume', 'adjoint24_consume'):
        source, value = [b.create_quantum_register(24, n) for n in ('source', 'value')]
        if label == 'product24_consume':
            GF24.emit_prefix(b, source, value)
        else:
            Direct._adjoint_consume(b, source, value, 2048)
        roles.update(source=wire_ids(source), value=wire_ids(value))
    else:
        raise ValueError(label)
    c = b.finish_circuit()
    path = directory / (label + '.kmb')
    c.to_file(str(path), format='kmb')
    return dict(label=label, path=str(path), sha256=sha(path), roles=roles,
                qubits=c.num_qubits, bits=c.num_bits,
                toffoli=c.operation_statistics().num_toffoli_like)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--intervals', type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    base = Splice.open_circuit(a.input, a.profile)
    windows = [(26440000, 26470000), (35675000, 35710000)]
    records = []
    for label in ('paired_divide_prefix', 'scalar_consume_closed',
                  'product24_consume', 'adjoint24_consume'):
        rec = build(label, a.out)
        template = Splice.open_circuit(rec['path'])
        before = list(template.operations(0, len(template.opcodes)))
        hits = []
        for lo, hi in windows:
            pos = lo
            while True:
                pos = base.opcodes.find(template.opcodes, pos, hi)
                if pos < 0:
                    break
                mapped = match(before, base.operations(pos, pos+len(before)))
                if mapped is not None:
                    qmap, bmap = mapped['qubits'], mapped['bits']
                    roles = {k: [bmap[q] for q in v] if k.endswith('_mask') else
                             [qmap[q] for q in v] for k, v in rec['roles'].items()}
                    hits.append(dict(start=pos, end=pos+len(before), mapping=mapped,
                                     roles=roles, condition_depth=
                                     base.opcodes[:pos].count(b'\x81')-
                                     base.opcodes[:pos].count(b'\x01')))
                pos += 1
        rec.update(operations=len(before), matches=hits)
        template.close()
        records.append(rec)
        print(json.dumps(dict(label=label, matches=[(h['start'],h['end']) for h in hits])), flush=True)
    peak_intervals = {}
    if a.intervals:
        with a.intervals.open() as f:
            header = f.readline().strip()
            assert header == 'q\tfirst\tlast\tabi'
            rows = [tuple(map(int, line.split())) for line in f]
        for op in (26458417, 26460853, 26481000, 35690810):
            peak_intervals[str(op)] = [r for r in rows if r[0] >= 840 and r[1] <= op <= r[2]]
    result = dict(status='EXACT_LATE_COMPONENT_CLASSIFICATION',
                  input_path=str(a.input), input_sha256=base.profile['raw_kmb_sha256'],
                  script_sha256=sha(__file__), templates=records, search_windows=windows,
                  source_files={str(Path(m.__file__)): sha(m.__file__) for m in
                                (Paired, Lender, GF24, Direct, Dual)},
                  scratch_intervals_at_selected_positions=peak_intervals,
                  modified_input=False, simulation_run=False,
                  elapsed_seconds=time.monotonic()-started,
                  scope='Exact source-block binding and conservative lifetime classification only; no global width claim.')
    (a.out/'classification.json').write_text(json.dumps(result, indent=2)+'\n')
    base.close()


if __name__ == '__main__':
    main()
