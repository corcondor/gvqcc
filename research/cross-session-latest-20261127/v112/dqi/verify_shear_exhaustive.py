#!/usr/bin/env python3
"""Independent bit-parallel exhaustive value, phase and classical-output proof."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).parent
def run(gates,qs,temps,measurement_bit,fresh_bit):
    live=[q for q in qs if q not in temps];n=len(live);N=1<<(n+1);mask=(1<<N)-1
    def variable(i):
        unit=(1<<(1<<i))-1;v=0
        for lo in range(1<<i,N,2<<i):v|=unit<<lo
        return v
    q={v:variable(i) for i,v in enumerate(live)};q.update({t:0 for t in temps});m=variable(n);bits={fresh_bit:m,measurement_bit:0};phase=0
    for raw,a,b,c,w,k in gates:
        op=raw&127;ctrl=mask if k<0 else bits[k]
        if op==0:phase^=ctrl
        elif op==16:phase^=ctrl&q[a]
        elif op==17:q[a]^=ctrl
        elif op==32:phase^=ctrl&q[a]&q[b]
        elif op==33:q[b]^=ctrl&q[a]
        elif op==34:
            d=ctrl&(q[a]^q[b]);q[a]^=d;q[b]^=d
        elif op==48:phase^=ctrl&q[a]&q[b]&q[c]
        elif op==49:q[c]^=ctrl&q[a]&q[b]
        elif op==50:
            d=ctrl&q[a]&(q[b]^q[c]);q[b]^=d;q[c]^=d
        elif op==64:bits[w]=bits.get(w,0)&(mask^ctrl)
        elif op==65:bits[w]=bits.get(w,0)|ctrl
        elif op==66:bits[w]=bits.get(w,0)^ctrl
        elif op==80:
            assert k<0 and w==measurement_bit
            phase^=m&q[a];q[a]=0;bits[w]=m
        else:raise ValueError(op)
    return q,phase,bits[measurement_bit],N
def main():
    plans=json.loads((ROOT/'dqi_shear_plans.json').read_text());rec=[]
    for p in plans['selected']:
        old=run(p['gates'],p['qubits'],p['temps'],p['m'],p['fresh_bit']);new=run(p['new_gates'],p['qubits'],p['temps'],p['m'],p['fresh_bit']);assert old==new
        rec.append({'first':p['first'],'end':p['end'],'old_ops':len(p['gates']),'new_local_ops':len(p['new_gates']),'presample_ops':1,'net_ops_delta':p['net_ops_delta'],'cases':old[3],'all_quantum_outputs_and_phase_and_measurement_bit_identical':True,'entry_zero':p['temps'],'old_paid':p['old_paid'],'new_paid':sum((g[0]&127) in (48,49,50) for g in p['new_gates'])})
    out={'status':'EXHAUSTIVE_VALUE_PHASE_CLASSICAL_PASS','circuit_sha256':plans['source_sha256'],'selected_islands':len(rec),'total_cases':sum(x['cases'] for x in rec),'records':rec,'scope':'Every arbitrary retained quantum input and both independent X-measurement outcomes; selected temporary starts zero. Full native stream and global clean entry checked separately.'}
    (ROOT/'dqi_shear_exhaustive.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()