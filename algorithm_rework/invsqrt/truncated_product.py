"""Evaluate narrowed products for direct fixed-point inverse-root phase."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from shared_curvature import Design, shift_round, exact_legal_screen


def truncated_product(a, b, cut):
    """Multiply while dropping the individual bit-products weighted < 2**cut."""
    out = a * b
    for j in range(cut):
        out -= (b & (1 << j)) * (a & ((1 << (cut-j)) - 1))
    return out


def tuned_coefficients(design, parity, ref, cut):
    p,g,q,fb,fc,f = list(asdict(design).values())
    l = 21-p
    r = np.arange(1 << l, dtype=np.int64)[None,:]
    offset = np.arange(1 << p, dtype=np.int64)
    left = 1.0 + offset / (1 << p)
    mult = 2 ** (-parity / 2)
    centers = (np.arange(1 << g) + 0.5) / (1<<g)
    c = np.rint(mult * 0.375 * (1.0 + centers) ** -2.5
                * 2.0 ** (fc - 2*p)).astype(np.int64)
    cg = c[offset >> (p-g)]
    left_y = mult / np.sqrt(left)
    right_y = mult / np.sqrt(left + 2.0**-p)
    b = np.rint((left_y - right_y + np.ldexp(cg.astype(float), -fc))
                * (1 << fb)).astype(np.int64)
    qr = shift_round(r,l-q)
    linear = shift_round(truncated_product(b[:,None], r, cut), l+fb-f)
    quadratic = shift_round(cg[:,None] * qr**2, 2*q+fc-f)
    correction = quadratic-linear
    target = ref.reshape(1 << p,1 << l) * (mult * (1 << f))
    remainder = target - correction
    a = np.rint((remainder.min(axis=1)+remainder.max(axis=1))/2).astype(np.int64)
    ratio = float(np.max(np.abs(target-(a[:,None]+correction))/target * (1 << 24)))
    return a,b,c,ratio


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    reference=1.0/np.sqrt(1.0+np.arange(1<<21)/(1<<21))
    findings=[]
    bounds=[]
    designs=[
        Design(7,7,10,27,26),
        Design(7,6,11,27,26),
        Design(8,5,8,27,26),
        Design(8,5,9,27,26),
        Design(8,6,8,27,26),
        Design(9,3,6,27,26),
    ]
    for design in designs:
        for cut in (0,8,10,11,12,13,14,15):
            coeffs=[tuned_coefficients(design, p, reference, cut) for p in range(2)]
            error=max(c[-1] for c in coeffs)
            w=max(int(np.max(c[1])).bit_length() for c in coeffs)
            width=21-design.prefix_bits
            omitted=sum(min(w,max(0,cut-j)) for j in range(width))
            result=dict(design=asdict(design), truncate_low_product_diagonals=cut,
                        error_over_tolerance=error, slope_total_pairs=w*width,
                        dropped_pairs=omitted, retained_pairs=w*width-omitted)
            print(json.dumps(result),flush=True)
            bounds.append(result)
            if error < .90:
                findings.append((result, [t[:3] for t in coeffs]))
    # Pareto anchors: maximize omitted pairs at p=7 and at p=8 with curvature sharing.
    summaries=[]
    for p,g in ((7,7),(7,6),(8,5),(9,3)):
        viable=[entry for entry in findings
                if entry[0]["design"]["prefix_bits"]==p
                and entry[0]["design"]["curvature_address_bits"]==g]
        if not viable:
            continue
        item,tabs=max(viable,key=lambda x:(x[0]["dropped_pairs"],-x[0]["error_over_tolerance"]))
        summaries.append(dict(**item, full_domain=exact_legal_screen(
            Design(**item["design"]), tabs,
            slope_product=lambda b,r: truncated_product(b,r,item["truncate_low_product_diagonals"])
          ),tables=[dict(intercept=t[0].tolist(),slope=t[1].tolist(),curvature=t[2].tolist()) for t in tabs]))
    args.output.write_text(json.dumps(dict(summaries=summaries,trials=bounds),indent=2)+"\n")
    for row in summaries:
        print(json.dumps({k:v for k,v in row.items() if k!='tables'}),flush=True)


if __name__=="__main__":
    main()
