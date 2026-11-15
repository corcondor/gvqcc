"""Compare the two observed default failures, without executing or resampling.

The executed plans are immutable evidence.  Their inherited descriptive labels
are documented below; group seed hashes and exact batch numbers determine the
actual inputs used by outcome_dqi_chart_paired.py.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read(name: str):
    return json.loads((ROOT / name).read_text())


def identity(name: str):
    data = (ROOT / name).read_bytes()
    return {"file": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def main():
    before_name = "score8_dqi_twochart_failed_ranges_before.json"
    after_name = "score8_dqi_twochart_failure_after.json"
    before, after = read(before_name), read(after_name)
    assert before["circuit_sha256"] == "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"
    assert after["circuit_sha256"] == "1d66248da1fc23e3a41817fe8a2b39cdbba957ba0aa908fe2aacea7e2b36e9e9"
    assert before["shots"] == 12800 and after["shots"] == 512
    for result in (before, after):
        assert result["value_errors"] == 2
        assert result["phase_errors"] == result["classical_changed_shots"] == 0

    def fkey(row):
        return row["group"], row["batch"], row["shot_in_batch"]

    old_failures = {fkey(row): row for row in before["failures"]}
    new_failures = {fkey(row): row for row in after["failures"]}
    assert set(old_failures) == set(new_failures)
    failures = []
    for key, row in sorted(new_failures.items()):
        old = old_failures[key]
        differences = [field for field in old if old[field] != row[field]]
        assert not (set(differences) - {"actual_phase"})
        failures.append({
            **{field: row[field] for field in (
                "group", "batch", "shot_in_batch", "absolute_shot",
                "sampled_error_weight", "rng_seed", "sim_seed",
                "value_error", "phase_error", "classical_changed", "expected_phase"
            )},
            "old_actual_phase": old["actual_phase"],
            "new_actual_phase": row["actual_phase"],
            "identical_input_syndrome_and_mask": True,
            "identical_syndrome_error_locations_and_ancilla_outputs": True,
            "differing_failure_fields": differences,
            "classification": "PREEXISTING_E4_VALUE_FAILURE_ON_IDENTICAL_INPUT",
        })

    old_batches = {(row["group"], row["batch"]): row for row in before["batches"]}
    batches = []
    for new in after["batches"]:
        old = old_batches[new["group"], new["batch"]]
        differences = [field for field in old if old[field] != new[field]]
        assert not (set(differences) - {"output_phases_sha256", "toffolis"})
        batches.append({
            "group": new["group"], "batch": new["batch"], "shots": 256,
            "input_hashes_identical": True,
            "output_syndrome_ancilla_mask_hashes_identical": True,
            "all_nonfailed_phases_equal_to_oracle_in_both_circuits": True,
            "old_toffolis": old["toffolis"], "new_toffolis": new["toffolis"],
            "differing_batch_fields": differences,
        })

    result = {
        "status": "PASS_SAME_TWO_PREEXISTING_VALUE_FAILURES",
        "official_pass": False,
        "new_official_evaluation": False,
        "resampled": False,
        "receipts": [identity(before_name), identity(after_name)],
        "executed_plans": [identity("score8_dqi_twochart_failed_ranges_before_plan.json"),
                           identity("score8_dqi_twochart_failure_after_plan.json")],
        "canonical_default_input_seed_sha256": after["circuit_sha256"],
        "localization_shots_in_old_e4": before["shots"],
        "reproduced_candidate_shots": after["shots"],
        "failures": failures,
        "matched_batches": batches,
        "metadata_caveat": {
            "inherited_descriptive_fields": ["created_utc", "independent_seed_label", "comparison_baseline_result"],
            "explanation": "The executed plans were copied from an earlier diagnostic plan. These descriptive fields retain old metadata and are not claims about the timing, cohort size or comparison source of this replay. The actual groups[].seed_sha256, groups[].batches, circuit identities, runner hash and stored numeric seeds define the executed work. Hash-bound plans are preserved unchanged.",
        },
        "interpretation": "Both failures observed in the new candidate default cohort already occur in unchanged e4 on identical inputs. This is a fixed-case diagnostic, not a full same-cohort equivalence proof or an official return. The phase of the weight-30 value-failing shot changes, as permitted by the stated limited equivalence claim; all value-correct shots in both replayed batches have the exact oracle phase. The measured R penalty compares distinct canonical default cohorts, not evidence that the new chart increases the physical decoder failure probability.",
    }
    path = ROOT / "score8_dqi_twochart_failure_comparison.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "failures": [
        {k: row[k] for k in ("batch", "shot_in_batch", "sampled_error_weight", "differing_failure_fields")}
        for row in failures
    ]}))


if __name__ == "__main__":
    main()
