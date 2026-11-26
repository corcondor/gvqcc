"""Expose what restricted-domain circuits do at excluded basis inputs.

No validity is asserted at these inputs. A nonzero HMR phase debt means that
flipping that measurement outcome changes the resulting phase by half a
turn, after its recorded correction. This is an explicit witness that the
legal-domain construction must not be advertised as a full-cube proof.
"""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'recovered/V79'))
from native_kmb import NativeKMB
MOD=1<<128

def replay(path,x):
    K=NativeKMB.read(path)
    state=[(x>>q)&1 for q in range(22)]+[0]*(K.header[1]-22)
    expected=state.copy()
    raw=dict(K.sections)[10]
    angles=[int.from_bytes(raw[i:i+16],'little') for i in range(0,len(raw),16)]
    phase=0;ri=0;pending=None;bad=[]
    for i,op in enumerate(K.ops):
        w=op.wires;g=op.raw
        if g==17:state[w[0]]^=1
        elif g==33:state[w[1]]^=state[w[0]]
        elif g==49:state[w[2]]^=state[w[0]]&state[w[1]]
        elif g==19:
            phase=(phase+angles[ri]*state[w[0]])%MOD
            ri+=1
        elif g==80:
            assert pending is None
            pending=(state[w[0]],i)
            state[w[0]]=0
        elif g in (144,160):
            assert pending is not None
            correction=state[w[0]]
            if g==160:correction&=state[w[1]]
            if correction!=pending[0]:
                bad.append(dict(hmr_instruction=pending[1],correction_instruction=i,
                                measured_bit=pending[0],correction_bit=correction))
            pending=None
        else:raise ValueError(op)
    assert pending is None and ri==len(angles)
    return dict(phase_all_measurement_outcomes_zero_u128=str(phase),
                input_and_work_restored=state==expected,
                nonzero_hmr_phase_debts=bad)

def main():
    reports=[]
    for name in ('ccx_min36','balanced30_36','cost_min36'):
        source=ROOT/'phaseopt'/f'{name}.kmb'
        candidate=ROOT/'theory/care'/f'{name}_care.kmb'
        examples=[]
        for x in (0,3145728,3670016):
            before=replay(source,x);after=replay(candidate,x)
            assert not before['nonzero_hmr_phase_debts']
            example=dict(x=x,excluded_from_legal_domain=True,
                         source=before,candidate=after)
            bad=after['nonzero_hmr_phase_debts']
            if bad:
                example['one_outcome_witness']=dict(
                    hmr_instruction=bad[0]['hmr_instruction'],
                    outcome=1,all_other_measurement_outcomes=0,
                    relative_phase_change_u128=str(1<<127))
            examples.append(example)
        reports.append(dict(source=str(source),candidate=str(candidate),examples=examples))
    out=ROOT/'theory/care/nonlegal_witnesses.json'
    out.write_text(json.dumps(reports,indent=2)+'\n')
    for r in reports:
        print(Path(r['candidate']).name,
              [(e['x'],len(e['candidate']['nonzero_hmr_phase_debts']),
                e['candidate']['input_and_work_restored']) for e in r['examples']])

if __name__=='__main__':main()
