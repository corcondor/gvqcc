#!/usr/bin/env python3
"""Independently check the exact lattice arithmetic used by sparse fitting."""
from fractions import Fraction
import argparse
import json
import math
from pathlib import Path


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();root=Path(__file__).resolve().parent
    cert=json.loads((root/'score6_invsqrt_modular_certificate.json').read_text());B=cert['integer_left_inverse'];A=cert['evaluation_rows']
    product=[[sum(b*c for b,c in zip(row,col)) for col in zip(*A)] for row in B]
    assert product==[[int(i==j) for j in range(39)] for i in range(39)]
    receipt=json.loads((root/'score8_invsqrt_sparse_phase_result.json').read_text());excluded=[]
    for row in receipt['rigorous_approximate_lattice_checks']:
        j=row['feature_index'];feature=cert['features'][j];angle=Fraction(feature['half_turns'])/2
        bound=sum(abs(b)*2*Fraction(math.isqrt((1<<130)//x)>>25,1<<64) for b,x in zip(B[j+1],cert['witness_xs']))
        distance=abs(angle-Fraction(round(angle*8),8))
        assert str(bound)==row['approximate_bound_turns'] and str(distance)==row['distance_turns']
        assert (distance>bound)==row['excluded']
        if feature['kind']=='rotation' and distance>bound:excluded.append(j)
    assert len(excluded)==19
    out={'status':'PASS_EXACT_INTEGER_AUDIT','left_inverse_shape':[39,40],'evaluation_shape':[40,39],'integer_product':'I_39','excluded_generic_features':excluded,'excluded_count':19,'nearest_lattice':'1/8 turns','bound':'sum_i abs(B_ji) * 2 * official_tolerance_i','scope':'Approximate changes on the same fixed phase predicates including constant phase. Baseline validity is established by the existing full official receipt; no unrestricted-circuit lower bound.'}
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))


if __name__=='__main__':main()
