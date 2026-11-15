"""Offline and exhaustive all-input check for integer shared-curvature inverse root."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path

import numpy as np

N = 21
MAX_X = 3_133_452
MASK64 = (1 << 64) - 1


@dataclass(frozen=True)
class Design:
    prefix_bits: int
    curvature_address_bits: int
    square_input_bits: int
    slope_frac_bits: int
    curvature_frac_bits: int
    phase_frac_bits: int = 30


def shift_round(values: np.ndarray, bits: int) -> np.ndarray:
    if bits <= 0:
        return values << -bits
    return (values + (1 << (bits - 1))) >> bits


def coefficients(design: Design, parity: int, reference: np.ndarray):
    p, g, q, fb, fc, f = list(asdict(design).values())
    l = N - p
    r = np.arange(1 << l, dtype=np.int64)[None, :]
    offset = np.arange(1 << p, dtype=np.int64)
    left = 1.0 + offset / (1 << p)
    mult = 2 ** (-parity / 2)
    if q:
        curvature_pos = (np.arange(1 << g) + 0.5) / (1 << g)
        c = np.rint(mult * 0.375 * (1.0 + curvature_pos) ** -2.5
                    * 2.0 ** (fc - 2*p)).astype(np.int64)
    else:
        c = np.zeros(1 << g, dtype=np.int64)
    cg = c[offset >> (p-g)]
    left_y = mult / np.sqrt(left)
    right_y = mult / np.sqrt(left + 2.0 ** -p)
    b = np.rint((left_y - right_y + np.ldexp(cg.astype(float), -fc))
                * (1 << fb)).astype(np.int64)
    qr = shift_round(r, l - q) if q else np.zeros_like(r)
    linear = shift_round(b[:, None] * r, l+fb-f)
    quadratic = shift_round(cg[:, None] * qr ** 2, 2*q+fc-f)
    correction = quadratic - linear
    target = reference.reshape(1 << p, 1 << l) * (mult * (1 << f))
    remainder = target - correction
    a = np.rint((remainder.min(axis=1) + remainder.max(axis=1))/2).astype(np.int64)
    prediction = a[:, None] + correction
    worst = float(np.max(np.abs(target-prediction) / target * (1 << 24)))
    return a, b, c, worst


def exact_legal_screen(design: Design, tables, slope_product=lambda b,r:b*r):
    # Same target rounding and tolerance definition as verify_submission_invsqrt.py.
    p,g,q,fb,fc,f=list(asdict(design).values())
    l=N-p
    worst=-1.
    min_margin=(1<<64)
    fails=0
    worst_x=0
    for e in range(N + 1):
        start=1 << e
        stop=min(1 << (e+1), MAX_X + 1)
        xs=np.arange(start,stop,dtype=np.int64)
        normalized=xs << (N-e)
        idx=(normalized >> l) & ((1<<p)-1)
        r=normalized & ((1<<l)-1)
        a,b,c=tables[e%2]
        qr=shift_round(r,l-q) if q else np.zeros_like(r)
        estimate = (a[idx] - shift_round(slope_product(b[idx],r),l+fb-f)
                    + shift_round(c[idx>>(p-g)]*qr**2,2*q+fc-f)).astype(np.uint64)
        units=estimate << (64-f-e//2)
        scale=1 << 130
        root=np.fromiter((math.isqrt(scale//x) for x in xs.tolist()),
                         dtype=object, count=len(xs))
        exact=np.fromiter((((x+1)>>1)&MASK64 for x in root),
                          dtype=np.uint64,count=len(xs))
        tol=np.fromiter((x>>25 for x in root),dtype=np.int64,count=len(xs))
        delta=(units-exact).view(np.int64)
        err=np.abs(delta)
        ratio=err/tol
        k=int(ratio.argmax())
        if ratio[k]>worst:
            worst=float(ratio[k])
            worst_x=int(xs[k])
        fails+=int((err>tol).sum())
        min_margin=min(min_margin, int((tol-err).min()))
    return dict(tested=MAX_X, failures=fails, max_error_over_tolerance=worst,
                worst_input=worst_x, min_margin_uint64_units=min_margin,
                min_margin_turns=math.ldexp(min_margin,-64))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    args=ap.parse_args()
    reference=1.0/np.sqrt(1.0+np.arange(1<<N)/(1<<N))
    trials=[]
    for p,g,q in [(7,5,8),(7,6,9),(7,7,10),(8,4,7),(8,5,8),(8,6,8),
                  (8,5,9),(9,2,6),(9,3,6),(9,4,7),(10,0,0),(11,0,0)]:
        for frac in [27,28,29]:
            d=Design(p,g,q,frac,26)
            coeffs=[coefficients(d, parity, reference) for parity in (0,1)]
            err=max(row[-1] for row in coeffs)
            tabs=[row[:-1] for row in coeffs]
            bw=max(int(np.max(t[1])).bit_length() for t in tabs)
            cw=max(int(np.max(t[2])).bit_length() for t in tabs)
            item=dict(design=asdict(d), normalized_max_error_over_tolerance=err,
                      slope_width_bits=bw, curvature_width_bits=cw,
                      linear_multiplier_dimensions=[N-p,bw],
                      coefficient_rows=2**(p+1), curvature_rows=2**(g+1) if q else 0)
            print(json.dumps(item),flush=True)
            trials.append((item,tabs))
    feasible=[(item,tabs) for item,tabs in trials
              if item["normalized_max_error_over_tolerance"]<.85]
    item, tabs=min(feasible,key=lambda x:(x[0]["coefficient_rows"],
          x[0]["linear_multiplier_dimensions"][1], x[0]["curvature_rows"],
          x[0]["design"]["square_input_bits"],x[0]["normalized_max_error_over_tolerance"]))
    d=Design(**item["design"])
    result={"trial_results": [item for item,_ in trials],
            "selected_design":item,
            "official_integer_phase_arithmetic":exact_legal_screen(d,tabs),
            "tables": [dict(intercept=a.tolist(),slope=b.tolist(),curvature=c.tolist())
                       for a,b,c in tabs]}
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ('trial_results','tables')},indent=2))


if __name__ == "__main__":
    main()
