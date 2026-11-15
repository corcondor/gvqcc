"""Check native common-control rewrites, including dirty CCX targets."""
import json
from itertools import product


def verify_max_fanout(max_targets: int = 7) -> dict:
    cases = 0
    for count in range(1, max_targets + 1):
        for a, b, enabled, *targets in product(range(2), repeat=count + 3):
            control = a & b & enabled

            expected_values = [t ^ control for t in targets]
            factored_values = targets.copy()
            for i in range(1, count):
                factored_values[i] ^= factored_values[0]
            factored_values[0] ^= control
            for i in range(1, count):
                factored_values[i] ^= factored_values[0]
            assert factored_values == expected_values

            expected_phase = sum(control & t for t in targets) % 2
            parity_into_first = sum(targets) % 2
            factored_phase = control & parity_into_first
            assert factored_phase == expected_phase
            cases += 1
    return {"max_targets": max_targets, "cases_per_identity": cases,
            "ccx_value_and_ccz_phase_equal": True}


if __name__ == "__main__":
    print(json.dumps(verify_max_fanout(), indent=2))
