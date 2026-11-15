#!/usr/bin/env python3
"""Read-only exact-template audit on the submitted public DQI821 circuit."""
import hashlib
import json
from pathlib import Path
import time
from collections import Counter
import dqi_ccx_peephole as shared
from theory_bilinear_verify import parse
from theory_bilinear_patch import source_ordered_gf12, wire_match

ROOT = Path(__file__).parent
BASE = ROOT.parent
SOURCE = BASE / 'dqi_inputs/821bf8d157c0.kmb'
EXPECTED = '821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3'

def independent_joint_pairs(out):
    """Require 60 distinct wires across a,b,c,z1,z2, not merely shared a."""
    blocks={b['start']:b for b in out['blocks']}
    eligible=[]
    for pair in out['adjacent_shared_operand_pairs']:
        if pair['gap_ops'] or not pair['common_input_untouched']:
            continue
        a,b=blocks[pair['first']],blocks[pair['second']]
        shared_regs={tuple(a['left']),tuple(a['right'])}&{tuple(b['left']),tuple(b['right'])}
        if len(shared_regs)!=1:continue
        common=next(iter(shared_regs))
        other1=next(reg for reg in (a['left'],a['right']) if tuple(reg)!=common)
        other2=next(reg for reg in (b['left'],b['right']) if tuple(reg)!=common)
        regs=[list(common),other1,other2,a['target'],b['target']]
        if len(set(sum(regs,[])))!=60:continue
        eligible.append({'first':pair['first'],'second':pair['second'],'common':list(common),
                         'other1':other1,'other2':other2,'target1':a['target'],'target2':b['target']})
    return eligible

def main():
    start = time.monotonic()
    h = hashlib.sha256()
    with SOURCE.open('rb') as f:
        for chunk in iter(lambda:f.read(8 << 20),b''):h.update(chunk)
    assert h.hexdigest() == EXPECTED
    profile=json.loads((BASE/'dqi_inputs/audit_actual_821/profile.json').read_text())
    assert profile['raw_kmb_sha256']==EXPECTED
    cert=json.loads((ROOT/'inverse_v2_actual_eea_product_certificate.json').read_text())
    inputs=json.loads((ROOT/'theory_bilinear_input_certificate.json').read_text())['records']
    old24=parse(ROOT/'inverse_v2_actual_eea_product.kmx')
    # Inner kernel is symmetric after the explicit conjugation layers.
    templates=[('gf12',source_ordered_gf12(inputs[0]['terms']),list(range(12)),list(range(12,24)),list(range(24,36))),
               ('gf24',old24[12:-12],cert['input_left'],cert['input_right'],cert['output_qubits_in_field_order'])]
    c=shared.BinaryCircuit(SOURCE,profile)
    out={'source_sha256':EXPECTED,'source_bytes':SOURCE.stat().st_size,'scope':'Exact sequence under injective wire renaming; no circuit edits', 'kernels':[], 'blocks':[]}
    try:
        for name,before,left,right,target in templates:
            pattern=bytes(o.opcode for o in before); pos=0; candidates=0;matches=0
            counts=Counter(o.opcode for o in before)
            while True:
                pos=c.opcodes.find(pattern,pos)
                if pos<0:break
                lo=pos;hi=lo+len(before);pos+=1;candidates+=1
                actual=list(c.operations(lo,hi))
                mapping=wire_match(before,actual)
                if mapping is None:continue
                rec={'kernel':name,'start':lo,'end':hi,'left':[mapping[q] for q in left],
                     'right':[mapping[q] for q in right],'target':[mapping[q] for q in target]}
                out['blocks'].append(rec); matches+=1
                if matches==1:print(json.dumps({'first_exact_match':rec,'CX':counts[0x21],'CCX':counts[0x31]}),flush=True)
            out['kernels'].append({'kernel':name,'opcode_candidates':candidates,'exact_matches':matches,'CX':counts[0x21],'CCX':counts[0x31]})
            print(json.dumps(out['kernels'][-1]),flush=True)
        out['blocks'].sort(key=lambda x:x['start'])
        pairs=[]
        for a,b in zip(out['blocks'],out['blocks'][1:]):
            if a['end']>b['start']:continue
            aset={tuple(a['left']),tuple(a['right'])};bset={tuple(b['left']),tuple(b['right'])}
            if not aset.intersection(bset):continue
            gap=list(c.operations(a['end'],b['start']))
            counts=Counter(o.opcode&0x7f for o in gap)
            common=set(q for reg in aset.intersection(bset) for q in reg)
            pure=all(o.opcode in (0x21,0x31) and o.bit is None and o.condition is None for o in gap)
            untouched=pure and all(o.qubits[-1] not in common for o in gap)
            pairs.append({'first':a['start'],'second':b['start'],'kernel_pair':[a['kernel'],b['kernel']],
                          'same_both_inputs':aset==bset,'gap_ops':len(gap),'gap_families':dict(counts),
                          'pure_CX_CCX_gap':pure,'common_input_untouched':untouched})
        out['adjacent_shared_operand_pairs']=pairs
        out['independent_joint_pair_placements']=independent_joint_pairs(out)
        out['summary']={'matched_blocks':len(out['blocks']),'adjacent_shared_operand_pairs':len(pairs),
                        'same_both_input_pairs':sum(p['same_both_inputs'] for p in pairs),
                        'pure_gap_shared_operand_pairs':sum(p['common_input_untouched'] for p in pairs),
                        'independent_joint_pairs':len(out['independent_joint_pair_placements']),
                        'proved_Toffoli_reduction':0}
    finally:c.close()
    out['seconds']=time.monotonic()-start
    target=ROOT/'symmetry_dqi_20261115_scan.json'
    target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'summary':out['summary'],'seconds':out['seconds'],'output':str(target)}),flush=True)

if __name__=='__main__':main()
