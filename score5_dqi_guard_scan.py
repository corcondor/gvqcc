#!/usr/bin/env python3
"""Read-only scan for the legacy guarded GF24 consuming-product return.

Emits isolated upstream templates and matches both opcodes and an injective
quantum/classical wire renaming. The base circuit is never modified. A negative
match excludes these literal templates, not arbitrarily optimized equivalents.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import kickmix as km
from dqi_ccx_peephole import BinaryCircuit
import kmb_profile as K

SOURCE = Path('/workspace/scratch/7f542e06b7cf/official_sources/Syed_v12/source/dqi_source/src/controller_work')
sys.path.insert(0, str(SOURCE/'night_c27/arithmetic'))
import gf24_arithmetic as A
sys.path.insert(0, str(SOURCE/'after_c5/arithmetic_t'))
import gf24_nested_norm as Nested

BASE_SHA = '6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def template(out, kind):
    b = km.CircuitBuilder()
    arithmetic = Nested if kind.startswith('nested_') else A
    if kind == 'guard_zero_then_shift':
        norm = b.create_quantum_register(12, 'norm')
        flag = b.create_quantum_register(1, 'flag')
        A.toggle_zero(b, norm, flag[0])
        b.cx(flag[0], norm[0])
    else:
        source = b.create_quantum_register(24, 'source')
        value = b.create_quantum_register(24, 'value')
        # emit_closing owns and frees the adopted mask, so it must be an
        # allocated temporary rather than a non-freeable named ABI register.
        mask = b.alloc_bits(24)
        record = arithmetic.make_record(b, mask, guarded=kind in ('guarded_closing', 'nested_guarded_closing'))
        arithmetic.emit_closing(b, source, value, record)
    circuit = b.finish_circuit()
    path = out/f'{kind}.kmb'
    circuit.to_file(path, format='kmb')
    return path, {'operations': len(circuit), 'qubits': circuit.num_qubits,
                  'bits': circuit.num_bits,
                  'static_T': circuit.operation_statistics().num_toffoli_like,
                  'sha256': sha(path)}


def match(before, actual):
    maps = ({}, {}, {}, {})
    q, qr, c, cr = maps
    def bind(x, y, f, r):
        if x is None or y is None:
            return x is y
        if (x in f and f[x] != y) or (y in r and r[y] != x):
            return False
        f[x] = y
        r[y] = x
        return True
    for old, new in zip(before, actual, strict=True):
        if old.opcode != new.opcode or old.angle != new.angle:
            return None
        if len(old.qubits) != len(new.qubits):
            return None
        if not all(bind(x, y, q, qr) for x, y in zip(old.qubits, new.qubits)):
            return None
        if not bind(old.bit, new.bit, c, cr) or not bind(old.condition, new.condition, c, cr):
            return None
    return {'qubits': q, 'bits': c}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/dqi.kmb'))
    ap.add_argument('--profile', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/profile.json'))
    ap.add_argument('--out', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score5_dqi_guard'))
    ap.add_argument('--receipt', type=Path, default=Path(__file__).with_suffix('.json'))
    args = ap.parse_args()
    begun = time.monotonic()
    args.out.mkdir(parents=True, exist_ok=True)
    profile = json.loads(args.profile.read_text())
    assert sha(args.base) == profile['raw_kmb_sha256'] == BASE_SHA
    base = BinaryCircuit(args.base, profile)
    result = {'base_sha256': BASE_SHA, 'base_read_only': True, 'templates': {}}
    try:
        for kind in ('guard_zero_then_shift', 'guarded_closing', 'unguarded_closing',
                     'nested_guarded_closing', 'nested_unguarded_closing'):
            path, info = template(args.out, kind)
            local = BinaryCircuit(path, K.profile(path, max_register_summaries=0))
            try:
                pattern = local.opcodes
                ops = list(local.operations(0, len(pattern)))
                assert match(ops, ops) is not None
                pos, opcode_hits, exact = 0, 0, []
                while True:
                    pos = base.opcodes.find(pattern, pos)
                    if pos < 0:
                        break
                    opcode_hits += 1
                    mapping = match(ops, base.operations(pos, pos + len(pattern)))
                    if mapping is not None:
                        mapping_blob = json.dumps(mapping, sort_keys=True, separators=(',', ':')).encode()
                        exact.append({'start': pos, 'end': pos + len(pattern),
                                      'quantum_map_entries': len(mapping['qubits']),
                                      'classical_map_entries': len(mapping['bits']),
                                      'mapping_sha256': hashlib.sha256(mapping_blob).hexdigest()})
                    pos += 1
                info.update(opcode_hits=opcode_hits, exact_hits=exact)
                result['templates'][kind] = info
                print(json.dumps({'template': kind, 'opcode_hits': opcode_hits,
                                  'exact_matches': len(exact)}), flush=True)
            finally:
                local.close()
    finally:
        base.close()
    result.update(elapsed_seconds=time.monotonic()-begun,
                  arithmetic_source_sha256=sha(A.__file__),
                  nested_arithmetic_source_sha256=sha(Nested.__file__),
                  scanner_source_sha256=sha(__file__),
                  masks_scope='Each entire closing matches all HMR outputs and every subsequent classical '
                              'target/condition use under one injective bit map. No masks are deleted or '
                              'transferred, because no candidate rewrite is performed.',
                  scope='Literal upstream guarded closing and zero-predicate/shift motif only; '
                        'no claim excluding transformed equivalent guards; no candidate or score improvement.')
    args.receipt.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'receipt': str(args.receipt), 'elapsed_seconds': result['elapsed_seconds']}))


if __name__ == '__main__':
    main()
