#!/usr/bin/env python3
"""Constructive two-pivot chart for an active zero numerator.

This is a classical polynomial construction plus a real reversible query
component, NOT a patched full decoder.  All upstream modules are imported
unchanged.  The chosen pivot is a public index, never an input identifier.
The source's Apache-2.0 notices remain in the upstream dependencies.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent / 'official_sources/Syed_v12/source/dqi_source/src/controller_work'
for relative in ('night_c27/arithmetic', 'night_c27/controller',
                 'after_c5/extractor_width', 'after_c5/arithmetic_t'):
    sys.path.insert(0, str(WORK / relative))
spec = importlib.util.spec_from_file_location('score5_failure_reference',
                                            WORK / 'night_c27/census/reference.py')
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def exact_divide(poly, divisor):
    result, remainder = R.divrem(poly, divisor)
    if remainder:
        raise ValueError('Chart did not establish polynomial divisibility')
    return result


def extract(numerator, denominator, weight, pivot):
    """Use S before pivot and S after pivot+1 only when N mod q_pivot=0.

    Ordinary M_i is [[P_i/q_i,1/q_i],[1,0]].  The alternative two-step
    block is S M_(i+1) M_i S.  Its first stored head is zero.  The second
    head is still a linear polynomial.  Both charts have determinant
    1/(q_i q_(i+1)).  No fixture or random seed enters this algorithm.
    """
    n, d = list(numerator), list(denominator)
    original = n[:], d[:]
    f = False
    heads, trace = [], []
    for i in range(weight):
        if i == pivot:
            f = R.quadratic_remainder(n, R.KAPPAS[i]) == (0, 0)
            if f:
                if R.quadratic_remainder(d, R.KAPPAS[i]) == (0, 0):
                    raise ValueError('Joint-zero pair is outside the coprime domain')
                n, d = d, n
        nr = R.quadratic_remainder(n, R.KAPPAS[i])
        dr = R.quadratic_remainder(d, R.KAPPAS[i])
        if nr == (0, 0):
            return {'success': False, 'stop': i, 'reason': 'unhandled zero numerator'}
        head = R.quadratic_div(dr, nr, R.KAPPAS[i])
        heads.append(head)
        n, d = exact_divide(R.add(d, R.product(head, n)), R.QUADRATICS[i]), n
        if i == pivot+1 and f:
            n, d = d, n
        trace.append({'node': i, 'degrees': [len(n)-1, len(d)-1],
                      'head': list(head)})
        if i != pivot:
            assert len(n) <= weight-i-1 and len(d) <= weight-i
    terminal = not n and len(d) == 1 and d[0] != 0
    n_back, d_back = n[:], d[:]
    for i in reversed(range(weight)):
        if i == pivot+1 and f:
            n_back, d_back = d_back, n_back
        n_back, d_back = d_back, R.add(R.product(R.QUADRATICS[i], n_back),
                                      R.product(heads[i], d_back))
        if i == pivot and f:
            n_back, d_back = d_back, n_back
    assert (n_back, d_back) == original
    return {'success': terminal, 'chart_selected': bool(f),
            'exact_polynomial_roundtrip': True, 'terminal': [n, d], 'trace': trace}


def emit_query(builder, head_i, head_j, n, d, flag, pivot, new_index,
               reverse=False):
    """Coherent query S^f M_j M_i S^f, with every input restored on return."""
    import raw_query_extractor as Q
    assert pivot+1 < new_index < 35
    builder.cswap(flag, n, d)
    if reverse:
        Q.query_step(builder, head_j, n, d, pivot+1, new_index, True)
        Q.query_step(builder, head_i, n, d, pivot, new_index, True)
    else:
        Q.query_step(builder, head_i, n, d, pivot, new_index)
        Q.query_step(builder, head_j, n, d, pivot+1, new_index)
    builder.cswap(flag, n, d)


def packed_mul(a, b):
    x = R.quadratic_mul((a & 4095, a >> 12), (b & 4095, b >> 12), 2048)
    return x[0] | (x[1] << 12)


def residue_view(h, k):
    return h ^ R.mul(h >> 12, 2*k)


def query_oracle(a, b, n, d, f, pivot, new_index):
    if f:
        n, d = d, n
    for old, head in ((pivot, a), (pivot+1, b)):
        public = R.KAPPAS[old] ^ R.KAPPAS[new_index]
        n, d = packed_mul(d ^ packed_mul(residue_view(head, new_index), n),
                          R.INV[public]), n
    if f:
        n, d = d, n
    return n, d


def native_query_check(output, pivot=13, new_index=15, count=4096):
    import kickmix as km
    import numpy as np
    b = km.CircuitBuilder()
    data = b.create_quantum_register(97, 'data')
    a, c, n, d, flag = data[:24], data[24:48], data[48:72], data[72:96], data[96]
    masks = b.create_classical_register(48, 'probe')
    emit_query(b, a, c, n, d, flag, pivot, new_index)
    prefix = b.finish_circuit()
    b.cz(masks[:24], n)
    b.cz(masks[24:], d)
    b.ccz(n[0], d[7], flag)
    emit_query(b, a, c, n, d, flag, pivot, new_index, True)
    pair = b.finish_circuit()
    for label, circuit in [('query_prefix', prefix), ('query_roundtrip_phase', pair)]:
        circuit.to_file(output / (label+'.kmb'), format='kmb')
    # Fixed engineering corpus, used once; no scoring salt or candidate search.
    rng = np.random.default_rng(2026111513)
    words = rng.integers(0, 1 << 24, (count, 4), dtype=np.uint32)
    flags = np.arange(count, dtype=np.uint32) & 1
    words[flags == 1, 0] = 0  # This chart's production invariant.
    expected = np.asarray([query_oracle(*map(int, row), int(f), pivot, new_index)
                           for row, f in zip(words, flags)], dtype=np.uint32)
    def bits(values, width=24):
        return ((np.asarray(values, dtype=np.uint32)[None, :] >>
                 np.arange(width, dtype=np.uint32)[:, None]) & 1).astype(bool)
    raw = np.zeros((97, count), dtype=bool)
    for k in range(4):
        raw[24*k:24*k+24] = bits(words[:, k])
    raw[96] = flags
    probes = rng.integers(0, 1 << 24, (count, 2), dtype=np.uint32)
    probe_bits = np.concatenate((bits(probes[:, 0]), bits(probes[:, 1])))
    phase = np.asarray([((int(x&m).bit_count()+int(y&t).bit_count()) & 1)
                        ^ ((int(x)&1)*((int(y)>>7)&1)*int(f))
                        for (x,y),(m,t),f in zip(expected,probes,flags)], dtype=bool)
    result=[]
    for label, circuit in [('prefix',prefix),('roundtrip_phase',pair)]:
        sim=km.Simulator(batch_size=count,seed=1513,counting_operations=True)
        sim.use_same_registers_as(circuit)
        sim.write_across_shots(circuit.register_data['data'],raw)
        sim.write_across_shots(circuit.register_data['probe'],probe_bits)
        sim.do(circuit)
        want=raw.copy()
        if label=='prefix':
            want[48:72]=bits(expected[:,0]);want[72:96]=bits(expected[:,1])
        actual=sim.read_across_shots(circuit.register_data['data'])
        ve=int(np.any(actual != want,axis=0).sum())
        pe=int((sim.read_phase_flipped_across_shots() !=
                (phase if label!='prefix' else np.zeros(count,dtype=bool))).sum())
        assert ve==pe==0
        result.append({'kind':label,'shots':count,'value_errors':ve,'phase_errors':pe,
                       'static_T':circuit.operation_statistics().num_toffoli_like,
                       'mean_T':sim.operation_statistics().num_toffoli_like/count,
                       'Q':circuit.num_qubits})
    return result


def main():
    import random
    started=time.monotonic()
    output=Path('/workspace/scratch/3815fb5fae06/score5_dqi_failure')
    output.mkdir(parents=True,exist_ok=True)
    records=json.loads((ROOT/'dqi_rare_failure_admission.json').read_text())['records']
    physical=[]
    for case in records:
        n,d=R.physical_pair(case['roots'],case['values'])
        result=extract(n,d,len(case['roots']),13)
        physical.append({'case_sha256':case['case_sha256'],'weight':len(case['roots']),
                         **result})
    assert physical[0]['chart_selected'] and physical[0]['success']
    rng=random.Random(202611151301)
    independent=[]
    for _ in range(128):
        weight=rng.randint(18,35)
        roots=rng.sample(range(1,4096),weight)
        values=[rng.randrange(1,4096) for _ in roots]
        n,d=R.physical_pair(roots,values)
        out=extract(n,d,weight,13)
        independent.append({'success':out['success'],
                            'chart_selected':out.get('chart_selected',False)})
    assert all(x['success'] for x in independent)
    native=native_query_check(output)
    result={'status':'PASS_CONSTRUCTIVE_POLYNOMIAL_AND_NATIVE_QUERY_COMPONENT_ONLY',
        'public_pivot':13,'physical_cases':physical,
        'polynomial_domain':'Coprime active N,D; the first selected zero-N pivot is '
                            '13; (N/q13) mod q14 is nonzero; remaining active '
                            'numerator residues stay nonzero. Simultaneous q13 '
                            'and q14 divisibility is not repaired by this two-step chart.',
        'independent_physical_cases':len(independent),
        'independent_failures':sum(not x['success'] for x in independent),
        'native':native,
        'query_propagation_extra_T_per_direction':41*24,
        'query_propagation_extra_T_roundtrip':41*24*2,
        'retained_chart_flag_qubits':1,
        'whole_Q_naive':890,
        'other_costs_unincluded':['first-pivot zero predicate and selection',
                                'polynomial synthesis alternate-shape component',
                                'matched measurement-phase debts and flag retirement'],
        'scope':'No complete decoder KMB. Native tests cover only the reversible query block. '
                'The known physical fixture is fixed by exact classical polynomial extraction '
                'and reconstruction, not yet by a full quantum circuit. The naive added '
                'query Toffoli cost alone exceeds one-failure sensitivity budget.',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'upstream_reference_sha256':hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest(),
        'elapsed_seconds':time.monotonic()-started}
    (ROOT/'score5_dqi_failure_twopivot.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('physical_cases',)},indent=2))


if __name__=='__main__':
    main()
