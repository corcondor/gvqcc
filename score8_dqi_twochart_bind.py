#!/usr/bin/env python3
"""Bind the new point69 cell to the unchanged native FFT coset64 view.

The probe includes both complete public coset transforms and the original
point70 and point71 cells. All original input-mask and data-wire identities
must match; only the clean scan ladder and local classical scratch may map.
No approximate instruction match is accepted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import dqi_ccx_peephole as Binary
import kmb_splice as Splice
from dqi_gauge_expand import load_original, initialize_builder, save_circuit
from score8_dqi_twochart import geometry


def match(old, actual):
    qs, qr, bs, br = {}, {}, {}, {}
    def bind(a,b,forward,reverse):
        if a is None or b is None:return a is b
        if a in forward and forward[a]!=b:return False
        if b in reverse and reverse[b]!=a:return False
        forward[a]=b;reverse[b]=a;return True
    for a,b in zip(old,actual):
        if a.opcode!=b.opcode or a.angle!=b.angle or len(a.qubits)!=len(b.qubits):return None
        if not all(bind(x,y,qs,qr) for x,y in zip(a.qubits,b.qubits)):return None
        if not bind(a.bit,b.bit,bs,br) or not bind(a.condition,b.condition,bs,br):return None
    return dict(qubits=qs,bits=bs)


def arrays(S, carry):
    # Fixed source recurrence: N,D = D,N+P from node33 down through node0.
    heads=[(S[2*i],S[2*i+1]) for i in range(35)]
    N=[carry[:12]];D=list(heads[34])
    for i in range(33,-1,-1):N,D=D,N+list(heads[i])
    assert len(D)==36 and len(N)==35
    return D,N


def build_probe(original,destination,reserved):
    import kickmix as km
    spec=geometry(original);old=spec['original']
    b,S,E=initialize_builder(reserved)
    carry=b.alloc_qubits(24);flag=b.alloc_qubits(1);ladder=b.alloc_qubits(10)
    D,K=arrays(S,carry)
    original.OriginalScan.emit_coset_view(b,D,64)
    original.OriginalScan.emit_coset_view(b,K,64)
    insertion=len(b.finish_circuit())
    pivot=km.array([km.b(i) for i in (49458,49457,49456,49455,49454,49453,49452,49451,49450,49449,49448,49447)])
    U=original.OriginalScan.geometry()['U'];M=original.OriginalScan.Finish.geometry()['M']
    for point in (70,71):
        index=old['plan'].points.index(point)
        mask=pivot if point==70 else E[index]
        divisor=original.F.mul(point,original.F.mul(original.OriginalScan.evaluate(U,point),original.OriginalScan.evaluate(M,point)))
        factor=original.F.mul(old['values'][index],original.F.invert(divisor))
        original.scale_mask(b,mask,factor)
        original.OriginalScan.point_cell(b,D[point^64],K[point^64],mask,ladder)
        original.scale_mask(b,mask,factor,inverse=True)
    info=save_circuit(b,destination/'coset64_probe.kmb')
    info.update(insertion_offset=insertion,
        point69_locator=[int(str(x)[1:]) for x in D[5]],
        point69_value=[int(str(x)[1:]) for x in K[5]],
        ladder=[int(str(x)[1:]) for x in ladder],
        pivot70=[int(str(x)[1:]) for x in pivot],
        original_classical_inputs=[int(str(x)[1:]) for x in E[old['plan'].points.index(71)]])
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--profile',type=Path)
    p.add_argument('--pieces',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();start=time.monotonic()
    import kickmix as km
    original=load_original(a.source_root)
    spec=geometry(original);old=spec['original']
    piece_meta=json.loads((a.pieces/'pieces.json').read_text())
    reserved=max(piece_meta['prefix']['bits'],piece_meta['suffix']['bits'])
    probe=build_probe(original,a.pieces,reserved)
    base=Splice.open_circuit(a.baseline,a.profile)
    assert base.profile['raw_kmb_sha256']=='e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355'
    c=Splice.open_circuit(a.pieces/'coset64_probe.kmb')
    before=list(c.operations(0,len(c.opcodes)));pattern=c.opcodes
    hits=[];pos=0;opcode_hits=0
    while True:
        pos=base.opcodes.find(pattern,pos)
        if pos<0:break
        opcode_hits+=1
        mapping=match(before,base.operations(pos,pos+len(pattern)))
        if mapping is not None:
            # Original quantum ABI data roles are fixed by the source recurrence.
            if any(q!=r for q,r in mapping['qubits'].items() if q<864):
                pos+=1;continue
            expected=probe['pivot70']+probe['original_classical_inputs']
            if any(mapping['bits'].get(bit)!=bit for bit in expected):
                pos+=1;continue
            hits.append(dict(start=pos,end=pos+len(pattern),mapping=mapping))
        pos+=1
    assert len(hits)==1,dict(exact_hits=len(hits),opcode_hits=opcode_hits)
    hit=hits[0];mapping=hit['mapping'];insert=hit['start']+probe['insertion_offset']
    assert base.opcodes[:insert].count(b'\x81')==base.opcodes[:insert].count(b'\x01')
    b,S,E=initialize_builder(reserved)
    b.alloc_qubits(49)
    locator=km.array([km.q(mapping['qubits'][q]) for q in probe['point69_locator']])
    value=km.array([km.q(mapping['qubits'][q]) for q in probe['point69_value']])
    ladder=km.array([km.q(mapping['qubits'][q]) for q in probe['ladder']])
    mask=km.array([km.b(i) for i in piece_meta['new_pivot']])
    U=original.OriginalScan.geometry()['U'];M=original.OriginalScan.Finish.geometry()['M']
    divisor=original.F.mul(69,original.F.mul(original.OriginalScan.evaluate(U,69),original.OriginalScan.evaluate(M,69)))
    factor=original.F.mul(spec['h_values'][spec['new_pivot_index']],original.F.invert(divisor))
    original.scale_mask(b,mask,factor)
    original.OriginalScan.point_cell(b,locator,value,mask,ladder)
    original.scale_mask(b,mask,factor,inverse=True)
    extra=save_circuit(b,a.pieces/'point69.kmb')
    assert extra['static_toffoli_like']==11 and extra['qubits']==889
    result=dict(status='EXACT_POINT69_INSERTION_BOUND',baseline_path=str(a.baseline),
        baseline_sha256=base.profile['raw_kmb_sha256'],probe=probe,
        unique_exact_coset64_match=hit,insertion_operation=insert,
        original_input_bit_ids_preserved=True,original_quantum_data_ids_preserved=True,
        point69_locator=[int(str(x)[1:]) for x in locator],
        point69_value=[int(str(x)[1:]) for x in value],
        clean_ladder=[int(str(x)[1:]) for x in ladder],
        normalized_mask_factor=factor,extra_cell=extra,
        expected_executed_T='11 if the new chart label is nonzero, otherwise0',
        existing_point70_mask='Original label, cleared exactly when the alternative wins',
        full_decoder_verified=False,seconds=time.monotonic()-start)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('unique_exact_coset64_match',)},indent=2),flush=True)
    base.close();c.close()


if __name__=='__main__':main()
