"""Paired, seed-independent-of-circuit study of classical gauge candidates.

The experiment generates the documented physical model: 4025 independent
uniform GF(2^12) residual masks and one fixed zero pivot.  No decoder sampling
seed, circuit hash, native quantum simulation or leaderboard result is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import time

import numpy as np


def choose(counts, candidates):
    capped = np.minimum(counts[candidates], 7)
    return int(candidates[int(np.argmax(capped))])


def exact_union_upper(n=4025, q=4096):
    """Exact finite union upper bound for full-label maximum occupancy.

    M=max(N0+1,N1,...,N(q-1)).  For every k,
    P(M>=k)<=min(1,P(N0>=k-1)+(q-1)*P(N1>=k)).
    Sum these rational tail bounds. All probabilities have denominator q**n.
    """
    denominator = q ** n
    masses = [pow(q - 1, n)]
    for j in range(n):
        numerator = masses[-1] * (n - j)
        divisor = (j + 1) * (q - 1)
        quotient, remainder = divmod(numerator, divisor)
        assert remainder == 0
        masses.append(quotient)
    assert sum(masses) == denominator
    tails = [0] * (n + 3)
    for j in range(n, -1, -1):
        tails[j] = tails[j + 1] + masses[j]
    numerator = sum(min(denominator, tails[k-1] + (q-1)*tails[k])
                    for k in range(1, n + 2))
    old_zero_numerator = denominator + n * (denominator // q)
    return {
        "full4096_expected_max_zeros_upper": numerator / denominator,
        "improvement_over_fixed_zero_upper": (numerator-old_zero_numerator) / denominator,
        "toffoli_saving_over_fixed_zero_upper": 11*(numerator-old_zero_numerator) / denominator,
        "denominator_power_of_two": int(math.log2(q)) * n,
        "upper_numerator_sha256": hashlib.sha256(str(numerator).encode()).hexdigest(),
        "arithmetic": "Exact integer finite binomial tails and union bound; decimals rounded for display.",
        "scope": "Uniform independent residual-mask model; bound is relative to fixed label0, so also bounds gain over gauge128.",
    }


def run(shots, seed):
    started = time.monotonic()
    rng = np.random.default_rng(seed)
    names = ["fixed128", "fixed256", "fixed512", "fixed1024", "fixed4096",
             "fixed128_plus_first32", "fixed128_plus_first64", "fixed128_plus_first128"]
    values = {name: [] for name in names}
    labels = {k: np.arange(k, dtype=np.int32) for k in (128,256,512,1024,4096)}
    input_digest = hashlib.sha256()
    invariant_cases = 0
    for _ in range(shots):
        words = rng.integers(0,4096,4025,dtype=np.uint16)
        input_digest.update(words.tobytes())
        counts = np.bincount(words, minlength=4096)
        counts[0] += 1
        for k in labels:
            chosen = choose(counts,labels[k])
            values[f"fixed{k}"].append(int(counts[chosen]))
        old = values["fixed128"][-1]
        for n in (32,64,128):
            candidates = np.concatenate((labels[128],words[:n].astype(np.int32)))
            chosen = choose(counts,candidates)
            count = int(counts[chosen])
            assert count >= old
            values[f"fixed128_plus_first{n}"].append(count)
            invariant_cases += 1
        assert all(values[f"fixed{k}"][-1] >= old for k in (256,512,1024,4096))
        invariant_cases += 4
    baseline = np.array(values["fixed128"],dtype=np.float64)
    rows = {}
    for name, counts in values.items():
        arr = np.array(counts,dtype=np.float64)
        delta = arr-baseline
        rows[name] = {
            "mean_zero_masks": float(arr.mean()),
            "paired_additional_zeros_vs128": float(delta.mean()),
            "paired_zero_delta_standard_error": float(delta.std(ddof=1)/math.sqrt(shots)),
            "predicted_mean_toffoli_saving_vs128": float(11*delta.mean()),
            "fraction_strictly_improved": float(np.mean(delta > 0)),
            "min_paired_zero_delta": int(delta.min()),
            "max_paired_zero_delta": int(delta.max()),
        }
    return {
        "status": "PAIRED_SELECTOR_MODEL_STUDY_COMPLETE",
        "shots": shots, "seed": seed, "input_sha256": input_digest.hexdigest(),
        "scope": "Synthetic classical mask model only; 11 saved scan Toffolis per additional zero. Not a full-decoder or leaderboard score.",
        "circuit_hash_or_verifier_seed_used": False,
        "pointwise_monotonicity_fixture_checks": invariant_cases,
        "pointwise_monotonicity_proof": "All original128 candidates are first. A strict capped-count replacement can happen only when incumbent count is below7; therefore a replacing candidate has strictly larger exact count. Ties retain incumbent.",
        "rows": rows, "exact_union_bound": exact_union_upper(),
        "seconds": time.monotonic()-started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shots",type=int,default=16384)
    p.add_argument("--seed",type=int,default=20261115)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    assert a.shots>=2 and not a.output.exists()
    # Only a digest of large integer witnesses is persisted.
    import sys
    sys.set_int_max_str_digits(0)
    result=run(a.shots,a.seed)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)


if __name__=="__main__":
    main()
