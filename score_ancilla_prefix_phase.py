#!/usr/bin/env python3
"""Exact classical phase accounting for measured prefix-XOR predicates.

This is an independently checked component, not a whole DQI contraction.
For h_i=zero(head_i), f_j=XOR_{i<=j}h_i, HMR masks m_j contribute
sum_j m_j f_j = sum_i (XOR_{j>=i}m_j)h_i. The ledger adds zero Toffolis,
zero extra quantum wires, and one classical accumulator. It assumes each
head predicate is available once in descending order before destruction.
All debt masks must exist before repayment starts; an HMR performed after
its final head predicate was destroyed cannot be paid by this schedule.
"""
from pathlib import Path
import json


class PrefixPhaseLedger:
    def __init__(self,builder,count):
        assert count>0
        self.builder=builder;self.count=count
        self.masks=[[] for _ in range(count)]
        self.accumulator=None;self.next=None

    def add_mask(self,index,mask):
        assert self.next is None and self.accumulator is None
        assert 0<=index<self.count and len(mask)==1
        self.masks[index].append(mask)

    def begin_reverse(self):
        assert self.next is None and self.accumulator is None
        self.accumulator=self.builder.alloc_bits(1)
        self.builder.bit_store(self.accumulator,False)
        self.next=self.count-1

    def pay_head(self,index,zero_head_predicate):
        assert self.next==index and self.accumulator is not None
        for mask in self.masks[index]:
            self.builder.cx(mask,self.accumulator)
            self.builder.free(mask)
        self.masks[index].clear()
        self.builder.cz(self.accumulator[0],zero_head_predicate)
        self.next-=1
        if self.next==-1:
            self.builder.bit_store(self.accumulator,False)
            self.builder.free(self.accumulator)
            self.accumulator=None

    def close(self):
        assert self.next==-1 and self.accumulator is None
        assert not any(self.masks)


def suffix_masks(masks):
    result=[0]*len(masks);running=0
    for index in reversed(range(len(masks))):
        running^=masks[index];result[index]=running
    return result


def algebra_check(count):
    # Equality of all entries of the two bilinear coefficient matrices is
    # a symbolic proof for every 2^(2*count) assignment, not random testing.
    checks=0
    for hpos in range(count):
        for mpos in range(count):
            direct=int(hpos<=mpos)
            masks=[int(i==mpos) for i in range(count)]
            transformed=suffix_masks(masks)[hpos]
            assert direct==transformed
            checks+=1
    return dict(status='PASS_BILINEAR_COEFFICIENT_IDENTITY',matrix_entries=checks,
                all_assignments_covered=1<<(2*count))


def native_check(count=17):
    import kickmix as km
    import numpy as np
    builder=km.CircuitBuilder()
    heads=builder.create_quantum_register(count,'head_predicates')
    probe=builder.create_classical_register(count,'probe')
    ledger=PrefixPhaseLedger(builder,count)
    for j in range(count):
        flag=builder.alloc_qubits(1)
        for i in range(j+1):builder.cx(heads[i],flag[0])
        builder.cz(probe[j],flag[0])
        mask=builder.alloc_bits(1);builder.hmr(flag,mask);builder.free(flag)
        ledger.add_mask(j,mask)
    ledger.begin_reverse()
    for j in reversed(range(count)):ledger.pay_head(j,heads[j])
    ledger.close()
    circuit=builder.finish_circuit()
    assert circuit.num_qubits==count+1
    assert circuit.operation_statistics().num_toffoli_like==0
    values=np.arange(1<<count,dtype=np.uint32)
    head_bits=((values[None,:]>>np.arange(count,dtype=np.uint32)[:,None])&1).astype(bool)
    prefixes=np.logical_xor.accumulate(head_bits,axis=0)
    rows=[]
    for seed in (1009,2141,3001):
        rng=np.random.default_rng(seed)
        probe_bits=rng.integers(0,2,head_bits.shape,dtype=np.uint8).astype(bool)
        expected=np.logical_xor.reduce(prefixes&probe_bits,axis=0)
        sim=km.Simulator(batch_size=len(values),seed=seed,counting_operations=True)
        sim.use_same_registers_as(circuit)
        sim.write_across_shots(heads,head_bits);sim.write_across_shots(probe,probe_bits)
        sim.do(circuit)
        assert np.array_equal(sim.read_across_shots(heads),head_bits)
        assert not sim.read_across_shots([km.q(count)]).any()
        assert np.array_equal(sim.read_phase_flipped_across_shots(),expected)
        rows.append(dict(seed=seed,cases=len(values),phase_errors=0,data_errors=0,scratch_errors=0))
    return dict(status='PASS_ISOLATED_NATIVE_COMPONENT',head_predicates=count,
                Q=circuit.num_qubits,T=circuit.operation_statistics().num_toffoli_like,
                instructions=len(circuit),runs=rows,
                scope='Already-available Boolean head predicates, no field zero-query synthesis, no DQI integration.')


def main():
    n=17;t=382115.5671582031;q=889
    # Concrete flag-free schedule: compute every forward flag locally, HMR;
    # rebuild seed flag from all n stable heads; on return rebuild f_j from
    # j+1 heads after the 24-helper arithmetic. Forward debts are batched;
    # local reverse erasure remains the existing zero(raw numerator) phase.
    extra_queries=n+n*(n+1)//2-(n-1)
    extra_t=23*extra_queries
    report=dict(algebra=algebra_check(n),native=native_check(n),
       optimistic_tail_schedule=dict(tail_slots=n,zero_query_T=23,
         added_seed_queries=n,reverse_queries=n*(n+1)//2,
         existing_reverse_queries=n-1,net_extra_queries=extra_queries,
         net_extra_static_T=extra_t,net_extra_mean_T=extra_t,
         score_win_budget_for_Q888=t*((q/(q-1))**2-1),
         optimistic_Q888_cost_ratio=((q-1)/q)**2*(t+extra_t)/t,
         whole_decoder_Q888_established=False,
         claim='This explicit phase-batched tail schedule exceeds the Q−1 budget; this is not an algorithmic lower bound.'))
    path=Path(__file__).with_name('score_ancilla_prefix_phase_result.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
