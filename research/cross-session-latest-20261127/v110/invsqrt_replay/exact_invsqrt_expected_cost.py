"""Exact expectations of classical guards under independent HMR outcomes."""
import argparse,hashlib,json,sys
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
import kickmix as km
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'invsqrt_joint'))
from classical_cleanup import ClassicalANF,load

@lru_cache(None)
def probability(poly):
    if not poly:return Fraction(0)
    if poly==frozenset([0]):return Fraction(1)
    support=0
    for m in poly:support|=m
    bit=support&-support
    zero=frozenset(m for m in poly if not m&bit)
    one=zero^frozenset(m^bit for m in poly if m&bit)
    return (probability(zero)+probability(one))/2

def main():
    ap=argparse.ArgumentParser();ap.add_argument('circuit',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    mod=load(ROOT/'extracted/evidence/invsqrt/prior/live_product_reuse_fast.py')
    c=km.Circuit.from_file(a.circuit);state=ClassicalANF(c.num_bits,mod.parse)
    paid=Fraction(0);ts=Fraction(0);rot=Fraction(0);hmr=Fraction(0);rows=[];maxsupport=0
    for i,l in enumerate(str(c).splitlines()):
        e=state.step(l)
        if e is None:continue
        n,qs,cb,d=mod.parse(l)
        if n not in ('CCX','CCZ','CSWAP','Z_POW','HMR'):continue
        p=probability(e[1]);support=0
        for monomial in e[1]:support|=monomial
        maxsupport=max(maxsupport,support.bit_count())
        if n in ('CCX','CCZ','CSWAP'):paid+=p
        elif n=='HMR':hmr+=p
        else:
            angle=Fraction(l.split()[2])
            if (angle*2).denominator==1:continue
            elif (angle*4).denominator==1:ts+=p
            else:rot+=p
        rows.append(dict(line=i,gate=n,probability=str(p)))
    margin=36584657
    import math
    eps=math.pi*margin/2**64/float(rot)
    rotation_equiv=float(rot)*(.56*math.log2(1/eps)+5.3)/4
    te=float(paid)+float(ts)/4+rotation_equiv
    rec=dict(status='EXACT_GUARD_EXPECTATIONS',circuit_sha256=hashlib.sha256(a.circuit.read_bytes()).hexdigest(),
             paid_toffoli_expected=str(paid),t_expected=str(ts),general_rotation_expected=str(rot),
             hmr_expected=str(hmr),max_guard_support=maxsupport,probability_cache_size=probability.cache_info().currsize,
             phase_margin_units=margin,expected_toffoli_equivalent=te,expected_score=c.num_qubits*te,
             scope='All classical guards expanded as Boolean ANF over independent potential HMR outcomes. Initial classical scratch is zero. Coherent branch correctness is checked separately.',gate_probabilities=rows)
    a.out.write_text(json.dumps(rec,indent=2)+'\n')
    print(json.dumps({k:v for k,v in rec.items() if k!='gate_probabilities'},indent=2))
if __name__=='__main__':main()