#!/usr/bin/env python3
"""Generate paired local templates and locate exact public third-pivot blocks."""
from pathlib import Path
import json
import time
import hashlib

import kickmix as km
import outcome_dqi_chart_third as C
import kmb_splice as Splice

ROOT = Path(__file__).resolve().parent


def build(module, label):
    b = km.CircuitBuilder()
    b.set_max_qubits(889)
    data = b.create_quantum_register(840, 'data')
    heads = (data[:24], data[24:48])
    current = data[48:72]
    bank = b.create_quantum_register(24, 'bank')
    flag = b.alloc_qubits(1)
    record = module.emit_prefix(b, heads, current, bank, flag[0])
    prefix_len = len(b.finish_circuit())
    saved_child_bits = [[int(str(bit)[1:]) for bit in rec.child_mask] for rec in record.inverses]
    saved_zero_bits = [int(str(bit)[1:]) for bit in getattr(record, 'zero_mask', [])]
    b.free(flag)
    module.emit_closing(b, heads, current, bank, record)
    circuit = b.finish_circuit()
    path = ROOT/f'outcome_dqi_chart_{label}_template.kmb'
    circuit.to_file(path, format='kmb')
    return {'file': str(path), 'prefix_ops': prefix_len, 'total_ops': len(circuit),
            'Q': circuit.num_qubits, 'bits': circuit.num_bits,
            'saved_child_bits': saved_child_bits, 'saved_zero_bits': saved_zero_bits,
            'T': circuit.operation_statistics().num_toffoli_like,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def match(before, actual):
    qs, qr, bs, br = {}, {}, {}, {}
    def bind(src, dst, forward, reverse):
        if src is None or dst is None:
            return src is dst
        if (src in forward and forward[src] != dst) or (dst in reverse and reverse[dst] != src):
            return False
        forward[src] = dst
        reverse[dst] = src
        return True
    for old, new in zip(before, actual):
        if old.opcode != new.opcode or old.angle != new.angle:
            return None
        if len(old.qubits) != len(new.qubits):
            return None
        if not all(bind(x, y, qs, qr) for x, y in zip(old.qubits, new.qubits)):
            return None
        if not bind(old.bit, new.bit, bs, br) or not bind(old.condition, new.condition, bs, br):
            return None
    return {'qubits': qs, 'bits': bs}


def main():
    begun = time.monotonic()
    # Same arithmetic alias used by the public production component. These
    # are isolated emitters, not a claimed gated production build.
    C.Original.Base.A = C.Norm.Arithmetic
    old = build(C.Original, 'old')
    new = build(C, 'new')
    template = Splice.open_circuit(old['file'])
    ranges = [('prefix', 0, old['prefix_ops']), ('return', old['prefix_ops'], old['total_ops'])]
    baselines = {
        '821': ROOT.parent/'dqi_inputs/821bf8d157c0.kmb',
        '9a82': Path('/workspace/scratch/3815fb5fae06/score3_gauge_sort_family/dqi_ccx480_gauge_sort4096.kmb'),
    }
    output = {'old_template': old, 'new_template': new, 'matches': {}}
    for label, path in baselines.items():
        base = Splice.open_circuit(path)
        found = {}
        for name, a, b in ranges:
            pattern = template.opcodes[a:b]
            before = list(template.operations(a, b))
            pos, hits = 0, []
            while True:
                pos = base.opcodes.find(pattern, pos)
                if pos < 0:
                    break
                mapping = match(before, base.operations(pos, pos+len(pattern)))
                if mapping is not None:
                    hits.append({'start': pos, 'end': pos+len(pattern), 'mapping': mapping})
                pos += 1
            found[name] = hits
            print(json.dumps({'baseline': label, 'part': name, 'exact_matches': len(hits)}), flush=True)
        output['matches'][label] = {'path': str(path), 'sha256': base.profile['raw_kmb_sha256'],
                                    'parts': found}
        base.close()
    template.close()
    output['elapsed_seconds'] = time.monotonic()-begun
    (ROOT/'outcome_dqi_chart_matches.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({'old': old, 'new': new, 'seconds': output['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
