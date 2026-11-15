#!/usr/bin/env python3
"""Test exact sign gauges already represented by the actual loader extension.

For each address, toggle any of the five first-batch word MSBs, then propagate
all32 choices through the existing fourteen tag-dependent transitions. This
tests a different route from recompiling a canonical zero-tag table: the entire
existing synthesis is held fixed. Integer angle orbits and final coordinate
signs determine equivalence; all HMR phase coefficients and scratch are tracked.
No file is replaced, no candidate or gate saving is assumed from the gauge.
"""
from pathlib import Path
import argparse
import hashlib
import json
import resource
import time
import numpy as np
import kickmix as km
from chemistry_affine_span_resynthesis import parse_line

BASE_SHA='5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357'


def pack(values):
    return int.from_bytes(np.packbits(np.asarray(values,dtype=np.uint8),bitorder='little').tobytes(),'little')


def unpack(value,n):
    return np.unpackbits(np.frombuffer(value.to_bytes((n+7)//8,'little'),dtype=np.uint8),bitorder='little')[:n]


def physical_equivalence(old,new,edges):
    """Exact integer predicate for U(new)=±U(old) on an ordered tree.

    Every child is introduced with zero amplitude, so magnitude equality of
    all final amplitudes requires each active split to have the same sine and
    cosine magnitudes. Those integer words lie in w' = ±w (mod128). Relative
    cosine/sine signs then propagate exactly. Angles at zero parents are free.
    """
    n=len(old);live=np.zeros((n,76),dtype=bool);live[:,0]=True
    rel=np.zeros((n,76),dtype=bool);valid=np.ones(n,dtype=bool)
    orbit_violations=np.zeros(n,dtype=np.int64)
    seen={0}
    for j,(p,c) in enumerate(edges):
        p,c=int(p),int(c);assert p in seen and c not in seen;seen.add(c)
        a=old[:,j].astype(np.int64);b=new[:,j].astype(np.int64)
        active=live[:,p].copy();rp=rel[:,p].copy()
        orbit=((a-b)%128==0)|((a+b)%128==0)
        orbit_violations+=active&~orbit;valid&=~active|orbit
        cos_a=(a>64)&(a<192);cos_b=(b>64)&(b<192)
        sin_a=a>128;sin_b=b>128
        rel[:,p]=rp^cos_a^cos_b;rel[:,c]=rp^sin_a^sin_b
        live[:,p]=active&(a%128!=64);live[:,c]=active&(a%128!=0)
    first=np.argmax(live,axis=1);global_sign=rel[np.arange(n),first]
    sign_bad=np.any(live&(rel!=global_sign[:,None]),axis=1)
    valid&=~sign_bad
    return valid,orbit_violations,sign_bad


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    table=a.source/'submission.npz'
    assert hashlib.sha256(table.read_bytes()).hexdigest()==BASE_SHA
    data=dict(np.load(table,allow_pickle=False));old=data['angle_words'].astype(np.uint8)
    assert old.shape==(1220,75)
    n=32*len(old);mask=np.repeat(np.arange(32,dtype=np.uint8),len(old))
    addresses=np.tile(np.arange(len(old),dtype=np.uint16),32)
    abits=[pack((addresses>>q)&1) for q in range(11)]
    ones=(1<<n)-1
    original=np.tile(old,(32,1));words=np.zeros_like(original)
    words[:,:5]=original[:,:5]^(((mask[:,None]>>np.arange(5))&1)*128).astype(np.uint8)
    incoming=words[:,:5];rows=[];invalid_phase=0;invalid_scratch=0;pins={}
    for k in range(1,15):
        path=a.source/f'angle_k_{k}.kmb';pins[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        circuit=km.Circuit.from_file(path)
        state=[0]*circuit.num_qubits;state[:11]=abits
        for j in range(5):
            for bit in range(8):state[11+8*j+bit]=pack((incoming[:,j]>>bit)&1)
        phase={};local_bad_phase=0;local_bad_scratch=0;measurements=0
        for pos,line in enumerate(str(circuit).splitlines()):
            gate,qs,condition=parse_line(line)
            if gate in {'X','CX','CCX','HMR','R','SWAP'}:assert condition is None
            if gate=='X':state[qs[0]]^=ones
            elif gate=='CX':state[qs[1]]^=state[qs[0]]
            elif gate=='CCX':state[qs[2]]^=state[qs[0]]&state[qs[1]]
            elif gate=='SWAP':state[qs[0]],state[qs[1]]=state[qs[1]],state[qs[0]]
            elif gate=='HMR':
                bit=int(line.split()[-1][1:]);local_bad_phase|=phase.get(bit,0)
                phase[bit]=state[qs[0]];state[qs[0]]=0;measurements+=1
            elif gate=='R':local_bad_scratch|=state[qs[0]];state[qs[0]]=0
            elif gate=='CZ':
                assert condition is not None and condition in phase
                phase[condition]^=state[qs[0]]&state[qs[1]]
            elif gate not in {'','REGISTER','APPEND_TO_REGISTER'}:raise AssertionError((pos,gate))
        assert state[:11]==abits
        for x in state[51:]:local_bad_scratch|=x
        for x in phase.values():local_bad_phase|=x
        invalid_phase|=local_bad_phase;invalid_scratch|=local_bad_scratch
        batch=np.zeros((n,5),dtype=np.uint8)
        for j in range(5):
            for bit in range(8):batch[:,j]^=unpack(state[11+8*j+bit],n)<<bit
        words[:,5*k:5*k+5]=batch;incoming=batch
        assert np.array_equal(batch[:1220],old[:,5*k:5*k+5]),('canonical mapping',k)
        row=dict(k=k,formal_HMR_variables=measurements,
                 phase_error_cases=local_bad_phase.bit_count(),scratch_error_cases=local_bad_scratch.bit_count())
        rows.append(row)
        print(json.dumps(row),flush=True)
    equal,orbit_bad,sign_bad=physical_equivalence(original,words,data['tree_edges'])
    exact_valid=equal&~unpack(invalid_phase|invalid_scratch,n).astype(bool)
    assert exact_valid[:1220].all()
    valid=exact_valid.reshape(32,1220)
    tag=((old[:,:5]>>6)^(old[:,:5]>>7))&1
    current_mask=(tag*(1<<np.arange(5))).sum(1)
    can_clear=valid[current_mask,np.arange(1220)]
    candidate_rows=np.any(valid[1:],axis=0)
    report=dict(status='EXISTING_EXTENSION_GAUGE_SCREEN_COMPLETE',
        source_npz_sha256=BASE_SHA,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        circuit_sha256=pins,proof_rows=n,noncanonical_rows=31*1220,
        offset_valid_address_counts=valid.sum(1).tolist(),
        addresses_with_any_nonzero_offset=int(candidate_rows.sum()),
        addresses_where_all_tags_can_be_cleared=int(can_clear.sum()),
        all_address_zero_tag_gauge_supported=bool(can_clear.all()),
        all_address_constant_offset_supported=[i for i in range(1,32) if valid[i].all()],
        noncanonical_orbit_failures=int(np.count_nonzero(orbit_bad[1220:])),
        noncanonical_final_sign_failures=int(np.count_nonzero(sign_bad[1220:])),
        phase_error_cases=invalid_phase.bit_count(),scratch_error_cases=invalid_scratch.bit_count(),
        gauge_definition='Change only first-batch MSBs by a5-bit per-address offset; use all later circuits unchanged; require the resulting complete Givens vector to equal original up to one global sign.',
        exactness='Modulo128 angle-orbit checks, integer quadrant signs, zero-amplitude propagation, and formal HMR phase coefficients. No floating tolerance is used.',
        limits=['Only existing-circuit extensions induced by these first-batch MSB offsets are tested.',
                'No general impossibility or minimum-Toffoli claim follows.',
                'A surviving gauge would still need a cheaper first-loader realization and full forward/reverse verification.'],
        new_candidate_emitted=False,toffoli_reduction=0,checks=rows,
        seconds=time.monotonic()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    np.savez_compressed(a.out/'allowed_offsets.npz',valid=valid)
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'checks','circuit_sha256'}},indent=2))


if __name__=='__main__':main()
