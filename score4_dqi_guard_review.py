#!/usr/bin/env python3
"""Independent focused review of the 16 proposed measurement-crossing merges.

Re-reads each original interval, checks every commutation on the CURRENT
rewritten local tape, and checks the dirty-target identity. Small native tests
compare values, classical outputs and phases with aligned HMR branches. It
does not edit the whole candidate or run the competition verifier.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json
from collections import Counter
from pathlib import Path
import kmb_profile as kp
from dqi_ccx_peephole import BinaryCircuit,Operation


def sha(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def commutes(first,other):
    assert first.opcode==0x31
    a,b,t=first.qubits;op=other.opcode&127;q=other.qubits
    if other.opcode in (0x01,0x81):return True
    if op in (0x00,0x40,0x41,0x42,0x06):return True
    if op in (0x10,0x13,0x20,0x30):return t not in q
    if op==0x11:return q[0] not in (a,b)
    if op in (0x21,0x31):return q[-1] not in (a,b) and t not in q[:-1]
    if op==0x22:return not set(q)&{a,b,t}
    if op==0x32:return not set(q[-2:])&{a,b,t} and t!=q[0]
    if op in (0x12,0x50):return q[0] not in (a,b,t)
    return False


def text(ops):
    rows=[]
    for o in ops:
        op=o.opcode&127
        if o.opcode==0x81:row=f'PUSH_CONDITION b{o.condition}'
        elif o.opcode==0x01:row='POP_CONDITION'
        else:
            assert op!=0x13 and not o.angle
            row=kp.OPCODES[op]
            row+=''.join(f' q{q}' for q in o.qubits)
            if o.bit is not None:row+=f' b{o.bit}'
            if o.condition is not None:row+=f' if b{o.condition}'
        rows.append(row)
    return '\n'.join(rows)+'\n'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    root=Path(__file__).parent
    source_sha=sha(args.input);assert source_sha=='9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1'
    profile=json.loads((root/'score4_dqi_cache_probe.profile.json').read_text());assert profile['raw_kmb_sha256']==source_sha
    scan=json.loads((root/'score4_guard_merge_dqi.json').read_text());assert scan['found']==16
    c=BinaryCircuit(args.input,profile)
    rows=scan['opportunities'];positions=sorted({x[k] for x in rows for k in ('first','second')})
    cursor=0;depth=0;depths={}
    for pos in positions:
        segment=c.opcodes[cursor:pos];depth+=segment.count(0x81)-segment.count(0x01);depths[pos]=depth;cursor=pos
    groups=[]
    for rec in sorted(rows,key=lambda x:x['first']):
        if groups and rec['first']<groups[-1]['end']:
            groups[-1]['end']=max(groups[-1]['end'],rec['second']+1);groups[-1]['pairs'].append(rec)
        else:groups.append(dict(start=rec['first'],end=rec['second']+1,pairs=[rec]))
    checked=0
    for a,b,t,u in itertools.product((0,1),repeat=4):
        old=(t^(a&b),u^(a&b));y=u^t;x=t^(a&b);y^=x
        assert (x,y)==old;checked+=1

    import kickmix as km
    import numpy as np
    rng=np.random.default_rng(2026111505);results=[];gate_checks=Counter();delta=Counter()
    for number,group in enumerate(groups):
        before=list(c.operations(group['start'],group['end']));after=before[:];proofs=[]
        for rec in group['pairs']:
            fi=next(i for i,o in enumerate(after) if o.source_index==rec['first'])
            si=next(i for i,o in enumerate(after) if o.source_index==rec['second'])
            assert fi<si
            first,second=after[fi],after[si]
            assert first.opcode==second.opcode==0x31 and depths[rec['first']]==depths[rec['second']]==0
            assert set(first.qubits[:2])==set(second.qubits[:2])==set(rec['controls'])
            assert len(set(first.qubits+second.qubits))==4
            assert first.qubits[2]==rec['targets'][0] and second.qubits[2]==rec['targets'][1]
            middle=after[fi+1:si]
            assert all(commutes(first,other) for other in middle)
            families=Counter(kp.OPCODES[o.opcode] for o in middle);gate_checks.update(families)
            fanout=Operation(0x21,(first.qubits[2],second.qubits[2]))
            after[fi:si+1]=middle+[fanout,first,fanout]
            proofs.append(dict(first=rec['first'],second=rec['second'],crossed_current_instructions=len(middle),
                               crossed_families=dict(families),all_gatewise_instrument_commutations=True))
        old_text,new_text=text(before),text(after)
        old,new=km.Circuit(old_text),km.Circuit(new_text)
        qids=sorted({q for o in before for q in o.qubits});bids=sorted({b for o in before for b in (o.bit,o.condition) if b is not None})
        quantum=km.array([km.q(q) for q in qids]);classical=km.array([km.b(b) for b in bids])
        qvalues=rng.integers(0,2,(len(qids),256),dtype=np.uint8).astype(bool)
        bvalues=rng.integers(0,2,(len(bids),256),dtype=np.uint8).astype(bool)
        sims=[]
        for tape in (old,new):
            sim=km.Simulator(batch_size=256,seed=2026111506,debug_print=False)
            sim.write_across_shots(quantum,qvalues)
            if bids:sim.write_across_shots(classical,bvalues)
            sim.do(tape);sims.append(sim)
        assert np.array_equal(sims[0].read_across_shots(quantum),sims[1].read_across_shots(quantum))
        if bids:assert np.array_equal(sims[0].read_across_shots(classical),sims[1].read_across_shots(classical))
        assert np.array_equal(sims[0].read_phase_flipped_across_shots(),sims[1].read_phase_flipped_across_shots())
        change=Counter(kp.OPCODES[o.opcode] for o in after);change.subtract(Counter(kp.OPCODES[o.opcode] for o in before));delta.update(change)
        results.append(dict(start=group['start'],end=group['end'],pairs=proofs,
                            original_local_sha256=hashlib.sha256(old_text.encode()).hexdigest(),
                            rewritten_local_sha256=hashlib.sha256(new_text.encode()).hexdigest(),
                            native_inputs=256,native_quantum_value_mismatches=0,native_classical_value_mismatches=0,native_phase_mismatches=0))
    c.close();assert delta['CCX']==-16 and delta['CX']==32 and all(v==0 for k,v in delta.items() if k not in ('CX','CCX'))
    out=dict(status='INDEPENDENT_LOCAL_INSTRUMENT_REVIEW_PASS',source_sha256=source_sha,
             scanner_sha256=sha(root/'score4_guard_merge_scan.cpp'),scanner_result_sha256=sha(root/'score4_guard_merge_dqi.json'),
             review_script_sha256=sha(__file__),merges=16,disjoint_intervals=len(groups),
             dirty_target_identity_inputs=checked,current_tape_commutation_counts=dict(gate_checks),
             instruction_delta={k:v for k,v in delta.items() if v},
             exact_proof=(
                 'Each earlier CCX is unconditional. Every intervening operation commutes '
                 'with it for every classical branch: controls are unwritten and its target '
                 'is unread, including phase and measurement operands. Moving it right '
                 'preserves each HMR Kraus operator and its recorded outcome. The adjacent '
                 'two-CCX dirty-target identity is then exact. Overlapping proposals are '
                 'rechecked after preceding local rewrites. No measurement is deleted or '
                 'moved. Hence all values and coherent phases are preserved for arbitrary '
                 'quantum inputs and all classical branches.'),
             native_scope='8 local circuits x256 arbitrary basis/classical inputs, aligned HMR branch seeds; not official scoring samples.',
             groups=results,whole_candidate_verified=False,official_verifier_run=False,score_claimed=False)
    args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('status','merges','disjoint_intervals','instruction_delta','current_tape_commutation_counts')}),flush=True)


if __name__=='__main__':main()
