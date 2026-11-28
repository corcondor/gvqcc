#!/usr/bin/env python3
"""Global liveness rearchitecture: postpone *creating* q34 until after two q36 HMRs.

The source branch starts immediately after q34's HMR at op 4389, when q34=0.
The 37-wire input is encoded into 36 wires by dropping zero q34 and storing
logical q36 on physical q34. From 4390 to 7351 the original q34 is not read;
its single AND generation at op7266 is postponed to after op7338, where the
old AND can be reconstructed from the *new* word representation with one CCX.
Original and candidate have equal CCX counts; this is a compositional 36Q
subprogram, NOT a whole-input inverse-sqrt oracle or a score improvement.
"""
from pathlib import Path
import os
from dataclasses import replace
import json,hashlib,sys
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from native_kmb import NativeKMB,Op
from build_prefix36 import byte_emit
REFERENCE=Path(os.environ.get('GVQCC_INVSQRT_KMB', BASE/'inputs/invsqrt.kmb'))
OUT=Path(__file__).parent/'outputs';OUT.mkdir(exist_ok=True)
START=4390; STOP=7352; ORIGINAL_MATERIALIZE=7266; LATE_POSITION=7339

def delayed_materialization():
    return [
        Op(0x21,(7,5)),
        Op(0x21,(15,5)),
        Op(0x21,(21,5)),
        Op(0x11,(5,)),
        Op(0x31,(33,5,34)),
        Op(0x11,(5,)),
        Op(0x21,(21,5)),
        Op(0x21,(15,5)),
        Op(0x21,(7,5)),
    ]

def construct(ref):
    ops=ref.ops
    assert ref.header[1]==37 and len(ops)==60766
    assert ops[START-1].raw==0x50 and ops[START-1].wires==(34,)
    assert ops[ORIGINAL_MATERIALIZE].raw==0x31 and ops[ORIGINAL_MATERIALIZE].wires==(20,33,34)
    assert all(34 not in o.wires for i,o in enumerate(ops[START:STOP],START) if i != ORIGINAL_MATERIALIZE)
    assert [o.wires for o in ops[7267:7274]]==[(21,20),(15,21),(13,20),(7,21),(5,21),(5,20),(21,)]
    assert [o.raw for o in ops[7267:7274]]==[0x22,0x21,0x21,0x21,0x21,0x21,0x11]
    # All read controls of the late product are not written before its synthesis.
    stable={33,5,7,15,21}
    for i,o in enumerate(ops[7274:LATE_POSITION],7274):
        name=o.raw&127; targets=[]
        if name in (0x11,0x50,0x12):targets=[o.wires[0]]
        elif name in (0x21,0x31):targets=[o.wires[-1]]
        elif name==0x22:targets=list(o.wires)
        elif name==0x32:targets=list(o.wires[1:])
        assert not stable.intersection(targets), (i,o)
    assert [i for i,o in enumerate(ops[7267:LATE_POSITION],7267) if 34 in o.wires]==[]
    assert all(36 not in o.wires for o in ops[7337:STOP])
    # same HMR transcripts and all classical instructions retained
    source=list(ops[START:STOP])
    out=[];srcmap=[]
    for i,o in enumerate(ops[START:STOP],START):
        if i==ORIGINAL_MATERIALIZE:continue
        if i==LATE_POSITION:
            for g in delayed_materialization():out.append(g);srcmap.append(None)
        out.append(replace(o,wires=tuple(34 if q==36 else q for q in o.wires)))
        srcmap.append(i)
    assert len(out)==STOP-START+8
    assert sum((o.raw&127)==0x31 for o in source)==sum((o.raw&127)==0x31 for o in out)
    assert sum((o.raw&127)==0x50 for o in source)==sum((o.raw&127)==0x50 for o in out)
    assert all(36 not in o.wires for o in out)
    assert [o.measurement for o in source if (o.raw&127)==0x50]==[o.measurement for o in out if (o.raw&127)==0x50]
    return source,out,srcmap

def generate():
    srcsha=hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
    assert srcsha=='bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b'
    ref=NativeKMB.read(REFERENCE)
    a,b,indices=construct(ref)
    part=OUT/'rematerialized_36Q_segment_ONLY.kmb'
    part.write_bytes(byte_emit(ref,b,36))
    assert NativeKMB.read(part).ops==b
    receipt=dict(reference_sha=srcsha,segment_source_ops={'begin':START,'end_exclusive':STOP},
       input_contract='virtual q34 = 0 at op4390; physical q34 holds virtual q36; q35 unchanged',
       output_contract='physical q34 recovers virtual q34; virtual q36=0 at op7352',
       virtual_original_CCX=sum((o.raw&127)==0x31 for o in a),
       remat_CCX=sum((o.raw&127)==0x31 for o in b),
       source_HMR=sum((o.raw&127)==0x50 for o in a),
       emitted_HMR=sum((o.raw&127)==0x50 for o in b),
       inserted_gates=9,omitted_original_gates=1,
       source_37Q_opcount=len(a),candidate_36Q_opcount=len(b),
       candidate_sha256=hashlib.sha256(part.read_bytes()).hexdigest(),
       formal_model='Universal Boolean identity at ops7266..7273, phase preserved by wire isomorphism; not full 36Q oracle',
       full_native_verifier_ran=False,full_36Q_circuit=False,score_improvement=False)
    (OUT/'construction.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
    return receipt
if __name__=='__main__':generate()
