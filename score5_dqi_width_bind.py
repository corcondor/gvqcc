#!/usr/bin/env python3
"""Bind the exact old chart template to a whole tape, without rewriting it."""
from pathlib import Path
import argparse
import json
import time
import kmb_splice as S
from outcome_dqi_chart_match import match


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--profile',type=Path)
    p.add_argument('--components',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();start=time.monotonic()
    receipt=json.loads(a.components.read_text())
    original=receipt['variants'][0]['chart_template']
    base=S.open_circuit(a.baseline,a.profile)
    old=S.open_circuit(original['path'])
    result=dict(status='EXACT_TEMPLATE_BINDING',input_path=str(a.baseline),
                input_sha256=base.profile['raw_kmb_sha256'],template=original,parts={})
    for label,lo,hi in [('prefix',0,original['prefix_ops']),
                       ('return',original['prefix_ops'],original['operations'])]:
        pattern=old.opcodes[lo:hi];before=list(old.operations(lo,hi));pos=0;hits=[]
        while True:
            pos=base.opcodes.find(pattern,pos)
            if pos<0:break
            mapping=match(before,base.operations(pos,pos+len(pattern)))
            if mapping is not None:
                depth=base.opcodes[:pos].count(b'\x81')-base.opcodes[:pos].count(b'\x01')
                assert depth==0
                hits.append(dict(start=pos,end=pos+len(pattern),mapping=mapping))
            pos+=1
        result['parts'][label]=hits
    assert all(len(v)==1 for v in result['parts'].values()),'Unique exact paired chart match required'
    prefix=result['parts']['prefix'][0];ret=result['parts']['return'][0]
    for q in [*range(72),*range(840,864)]:
        assert prefix['mapping']['qubits'][q]==ret['mapping']['qubits'][q]
    for row in original['saved_child_masks']:
        for b in row:assert prefix['mapping']['bits'][b]==ret['mapping']['bits'][b]
    result.update(elapsed_seconds=time.monotonic()-start,
                  persistent_quantum_roles_match=True,saved_child_mask_roles_match=True,
                  whole_tape_rewritten=False)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('parts','template')},indent=2))
    print(json.dumps({k:[(v['start'],v['end']) for v in hits] for k,hits in result['parts'].items()}))
    base.close();old.close()


if __name__=='__main__':main()
