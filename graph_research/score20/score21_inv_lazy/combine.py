"""Combine the two overlapping dense phase rewrites with conditional materialization."""
import argparse
from collections import defaultdict
from hashlib import sha256
from itertools import product as cartesian
import json
from pathlib import Path
import re

import kickmix as km
import numpy as np

from lazy import PIN, DOMAIN, DATA, PHASE, apply, make_trace, parse, product, tracks_for

START=22310
SECOND=22351
OPEN=22354
CLOSE=22392
END=22401

def render(lines,track,validated):
    rows={r['start']:r for r in validated}
    assert START in rows and SECOND in rows
    a=rows[START]; b=rows[SECOND]
    bits_max=max(int(i) for l in lines for i in re.findall(r'\bb(\d+)\b',l))
    raw_bit=f'b{bits_max+1}'
    before=defaultdict(list)
    after=defaultdict(list)
    after[OPEN].append(lines[START])
    before[CLOSE]+=[f'HMR q37 {raw_bit}',f'CZ q28 q34 if {raw_bit}']
    for row in (a,b):
        for form in row['corrections']:
            for cut,label in form['terms']:
                if label.startswith('PARITY_CCZ ') and row is a:
                    continue
                active={track[3][s] for s in track[0][cut]}
                guards=set(tuple(k) for k in form['guards'])-active
                for bit,_ in sorted(guards):
                    after[cut].append(f'PUSH_CONDITION if {bit}')
                if label.startswith('PARITY_CCZ '):
                    _,x,y,z,*others=label.split()
                    affine=[f'CX {q} {z}' for q in others]
                    after[cut]+=affine+[f'CCZ {x} {y} {z}']+affine[::-1]
                else:
                    after[cut].append(label)
                after[cut]+=['POP_CONDITION']*len(guards)
    middle=[]
    for i in range(START,END+1):
        middle.extend((i,l) for l in before[i])
        if i not in (START,SECOND):
            middle.append((i,lines[i]))
        middle.extend((i,l) for l in after[i])
    return middle,raw_bit

def simulate(records,state,one,original_bits,internal_value,internal):
    state=list(state)
    record={}
    phase=0
    scopes=[]
    enabled=True
    for i,line in records:
        op,qs,b= parse(line)
        if op=='PUSH_CONDITION':
            scopes.append(enabled)
            enabled=enabled and record[b]
            continue
        if op=='POP_CONDITION':
            enabled=scopes.pop()
            continue
        if not enabled or (b and not record[b]):
            continue
        if op=='HMR':
            bit=line.split()[2]
            measured=internal_value if bit==internal else original_bits[i]
            record[bit]=measured
            if measured:
                phase^=state[qs[0]]
        if op in PHASE|{'NEG'}:
            phase^=product(state,qs,one)
        else:
            assert op in DATA
            apply(op,qs,state,one)
    assert not scopes
    return state,phase,{k:v for k,v in record.items() if k!=internal}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--dense',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    assert sha256(args.source.read_bytes()).hexdigest()==PIN
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    gates=list(map(parse,lines))
    rows=json.loads(args.dense.read_text())
    assert rows['source']==PIN
    patched,internal=render(lines,tracks_for(gates,lines),rows['validated'])
    old=list(enumerate(lines[START:END+1],start=START))
    xs=np.arange(1,DOMAIN+1,dtype=np.uint32)
    state=next(x for i,x in enumerate(make_trace(gates,xs)) if i==START-1)
    assert not state[37]
    one=(1<<len(xs))-1
    writes=[i for i,line in old if line.startswith('HMR')]
    for version in cartesian((0,1),repeat=len(writes)):
        base=simulate(old,state,one,dict(zip(writes,version)),0,internal)
        for new in (0,1):
            actual=simulate(patched,state,one,dict(zip(writes,version)),new,internal)
            assert actual==base,(version,new)
    original=chr(10).join(lines[:START]+[l for _,l in patched]+lines[END+1:])+chr(10)
    circuit=km.Circuit(original)
    assert circuit.num_qubits==46 and circuit.operation_statistics().num_toffoli_like==1550
    kmb=args.out.with_suffix('.kmb')
    circuit.to_file(kmb,format='kmb')
    receipt=dict(source=PIN,candidate=sha256(kmb.read_bytes()).hexdigest(),
                 interval=(START,END),full_domain=DOMAIN,all_outcome_assignments=2**(len(writes)+1),
                 exact_expected_toffoli_change=-1,phase='exact',
                 source_unconditional=[START,SECOND],new_one_guard_paid=2,
                 original_hmr_measurements=writes,new_hmr_bit=internal,
                 replacement=[l for _,l in patched])
    args.out.write_text(json.dumps(receipt,indent=2)+'\n')
    print({k:v for k,v in receipt.items() if k!='replacement'},flush=True)

if __name__=='__main__':
    main()
