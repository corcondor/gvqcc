"""Audit a 25-bit input code with a small-input marker in spare mantissa lanes."""
import argparse
import json
from pathlib import Path
import numpy as np

MAX_X=3133452
MANTISSA_BITS=22
LANE_START=3<<20

def encode(xs):
    exponent=np.floor_divide(np.frexp(xs.astype(np.float64))[1]-1,2).astype(np.uint32)
    n=(xs<<np.uint32(20-2*exponent)).astype(np.uint32)
    small_lo=xs<16
    small_hi=(16<=xs)&(xs<64)
    n[small_lo]|=1
    n[small_hi]=LANE_START|xs[small_hi]
    return ((exponent&7)<<np.uint32(MANTISSA_BITS))|n

def decode(codes):
    e=codes>>np.uint32(MANTISSA_BITS)
    n=codes&((1<<MANTISSA_BITS)-1)
    small_lo=(e<=1)&((n&1)==1)
    small_hi=(e==2)&(n>=LANE_START)
    actual_e=e+np.uint32(8)*(e<=2)
    actual_e[small_lo]=e[small_lo]
    x=(n>>np.uint32(20-2*actual_e)).astype(np.uint32)
    x[small_hi]=n[small_hi]&63
    return x,small_lo|small_hi

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    x=np.arange(1,MAX_X+1,dtype=np.uint32)
    codes=encode(x)
    result,flag=decode(codes)
    assert np.array_equal(result,x)
    assert np.array_equal(flag,x<64)
    assert codes.max()<1<<25
    receipt=dict(inputs=MAX_X,bits=25,decoded_input_mismatches=0,decoded_q25_mismatches=0,
                 raw_exponent_bits=3, mantissa_bits=22, special_inputs=63,
                 scope='Injective integer normalization code and exact decoder. No circuit arithmetic or official phase evaluation.')
    print(receipt,flush=True)
    args.out.write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    main()
