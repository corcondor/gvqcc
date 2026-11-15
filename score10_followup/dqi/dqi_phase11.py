#!/usr/bin/env python3
# Derived from phase_inverse12.py, Copyright 2026 Syed Asad Ali.
# SPDX-License-Identifier: Apache-2.0
"""Use one fewer helper for the fixed inverse phase via two terminal CCZs."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

def leaf_phase11(builder, C, B):
    """Apply the inverse leaf phase with three live AND values."""
    import inverse_phase27 as base
    from field_tensor import invert_binary_columns, parity_pivot
    from tower_inverse import apply_inplace_linear, rows_from_columns

    apply_inplace_linear(builder, B, base.GRAM_ROWS)
    signals = list(C)
    pending = []
    for left, right in base.LEAF_GATES[:3]:
        parent_wires = tuple(signals)
        view, undo = base._view_pair(builder, parent_wires, left, right)
        target = builder.alloc_qubits(1)
        builder.init_and(view[0], view[1], target[0])
        apply_inplace_linear(builder, view, undo)
        pending.append((parent_wires, left, right, target))
        signals.append(target[0])

    for bit, form in enumerate(base.LEAF_OUTPUTS):
        for j, signal in enumerate(signals):
            if form >> j & 1:
                builder.cz(B[bit], signal)

    # The remaining two products share the same seven available parent
    # wires. Neither uses the other. Contract each product with the parity
    # of all its output-phase users before emitting its CCZ.
    for index, (left, right) in enumerate(base.LEAF_GATES[3:], start=7):
        assert max(left, right) < (1 << len(signals))
        weight = sum(((form >> index) & 1) << bit
                     for bit, form in enumerate(base.LEAF_OUTPUTS))
        assert weight
        view, undo = base._view_pair(builder, signals, left, right)
        phase_wire = parity_pivot(builder, B, weight)
        builder.ccz(phase_wire, view[0], view[1])
        parity_pivot(builder, B, weight)
        apply_inplace_linear(builder, view, undo)

    for parents, left, right, target in reversed(pending):
        view, undo = base._view_pair(builder, parents, left, right)
        builder.del_and(view[0], view[1], target[0])
        builder.free(target)
        apply_inplace_linear(builder, view, undo)
    apply_inplace_linear(builder, B,
                         invert_binary_columns(rows_from_columns(base.GRAM_ROWS)))

def verify(work, out):
    sys.path.insert(0,str(work/'night_c27/arithmetic'))
    import phase_inverse12 as phase
    from quantum_reciprocal import bit_matrix
    field = km.GF2Field(12)
    original_leaf = phase._leaf_phase12
    values = np.arange(4096, dtype=np.int64)
    inverses = np.array([field.invert(int(x)) if x else 0 for x in values],
                        dtype=np.int64)
    rng = np.random.default_rng(2026111503)
    probes = rng.permutation(4096)
    original_scale=phase.Base._classical_scale
    records = []
    for masked in (False,True):
        for new in (False,True):
            builder=km.CircuitBuilder()
            x=builder.create_quantum_register(12, 'source')
            dirty=builder.create_quantum_register(7, 'arbitrary_preserved')
            mask=builder.create_classical_register(12,'phase_mask') if masked else None
            phase._leaf_phase12=leaf_phase11 if new else original_leaf
            if masked:
                # Adapt the already verified width-generic classical field
                # scale from the previous GF64 phase component.
                from dqi_next_arithmetic_classical_scale import classical_scale_inplace
                phase.Base._classical_scale=classical_scale_inplace if new else original_scale
            try:
                if masked:
                    phase.phase_inverse_twelve_polynomial(builder,x,mask)
                    expected=[(int(y)&int(m)).bit_count()&1 for y,m in zip(inverses,probes)]
                else:
                    phase.fixed_inverse_trace12(builder,x)
                    expected=[phase.Base._trace(int(y)) for y in inverses]
            finally:
                phase._leaf_phase12=original_leaf
                phase.Base._classical_scale=original_scale
            tape=builder.finish_circuit()
            scratch=[km.q(i) for i in range(19,tape.num_qubits)]
            assert len(scratch)==(11 if new else 12)
            assert tape.operation_statistics().num_toffoli_like==27
            bystanders=rng.integers(0,128,len(values))
            for seed in (7,442,1917,15514):
                sim=km.Simulator(batch_size=len(values),seed=seed)
                sim.use_same_registers_as(tape)
                sim.write_across_shots(x,bit_matrix(values,12))
                sim.write_across_shots(dirty,bit_matrix(bystanders,7))
                if masked:
                    sim.write_across_shots(mask,bit_matrix(probes,12))
                sim.do(tape)
                assert np.array_equal(sim.read_across_shots(x),bit_matrix(values,12))
                assert np.array_equal(sim.read_across_shots(dirty),bit_matrix(bystanders,7))
                assert not sim.read_across_shots(scratch).any()
                assert np.array_equal(sim.read_phase_flipped_across_shots(),np.asarray(expected,dtype=bool))
                if masked:
                    assert np.array_equal(sim.read_across_shots(mask),bit_matrix(probes,12))
            buffer=io.BytesIO()
            tape.to_file(buffer,format='kmb')
            payload=buffer.getvalue()
            name=('masked' if masked else 'fixed')+('_phase11' if new else '_original')
            (out/(name+'.kmb')).write_bytes(payload)
            records.append(dict(name=name, helpers=len(scratch), qubits=tape.num_qubits,
                                toffoli=27, phase_oracle_errors=0,
                                shots=4*len(values), sha256=hashlib.sha256(payload).hexdigest()))
    return dict(status='PASS_COMPONENT_ONLY',component_records=records,
                total_shots=sum(r['shots'] for r in records),
                whole_dqi_output=None,
                source_hashes={Path(m.__file__).name:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                    for m in (phase,phase.Base)})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--arithmetic',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    sys.path.insert(0,str(a.arithmetic))
    a.out.mkdir(exist_ok=True)
    report=verify(a.work,a.out)
    print(json.dumps(report,indent=2))
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
