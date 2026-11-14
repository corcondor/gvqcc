"""Bounded, read-only counterexample screen for four rolling-flag decoders.

Uses existing pure-Python physical and first-three-chart boundary references.
The reference function is observed with sys.settrace, never rewritten. Curated
physical fixtures are counterexample inputs, not probability samples.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict, deque
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import resource
import signal
import sys
import time


NAMES = (
    "whole_word_zero_tests",
    "half_word_zero_tests",
    "half_zeros_low_bits_and_parities",
    "any_affine_parity_of_head_carry_and_half_zero_tests",
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def halves(head, carry):
    return (head & 4095, head >> 12, carry & 4095, carry >> 12)


def features(name, node, head, carry):
    words = halves(head, carry)
    zeros = tuple(int(x == 0) for x in words)
    if name == NAMES[0]:
        return (node, int(head == 0), int(carry == 0))
    if name == NAMES[1]:
        return (node, *zeros)
    if name == NAMES[2]:
        return (node, *zeros, *(x & 1 for x in words),
                *(x.bit_count() & 1 for x in words))
    raise KeyError(name)


def affine_features(head, carry):
    # Constant, all 48 source bits, four whole-half zero predicates.
    zeros = sum((int(x == 0) << k) for k, x in enumerate(halves(head, carry)))
    return 1 | (head << 1) | (carry << 25) | (zeros << 49)


def limits(seconds):
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    def expired(_signum, _frame):
        raise TimeoutError("bounded wall-time budget reached")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, min(float(seconds), 118.0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=118.0)
    parser.add_argument("--max-trajectories", type=int, default=20000)
    args = parser.parse_args()
    started = time.monotonic()
    limits(args.seconds)
    root = Path(__file__).resolve().parent.parent
    work = root / "official_sources/Syed_v12/source/dqi_source/src/controller_work"
    physical_path = work / "night_c27/arithmetic/panel_audit/physical_boundary_oracle.py"
    carry_path = work / "after_v3/blocks/v6/boundary_scale_first3.py"
    fixture_path = work / "after_v3/blocks/v6/runs/first3-full/fixtures.json"
    tracked = [physical_path, carry_path, fixture_path,
               work / "night_c27/census/reference.py",
               work / "after_c5/extractor_width/direct_carry_scalar_screen.py"]
    before = {str(p.relative_to(root)): digest(p) for p in tracked}
    report = {
        "status": "INITIALIZING",
        "source_sha256": before,
        "script_sha256": digest(__file__),
        "scope": "Existing admitted physical fixtures, cutoff18, exact first-three-chart scalar replay",
        "not_population_sampling": True,
        "native_simulator_used": False,
        "full_circuit_validation": False,
        "candidate_files_modified": False,
        "memory_limit_bytes": 1 << 30,
        "wall_limit_seconds": min(args.seconds, 118.0),
        "max_trajectories": min(args.max_trajectories, 20000),
        "candidate_definitions": {
            NAMES[0]: "At a fixed public node: zero(head), zero(carry)",
            NAMES[1]: "At a fixed public node: zero of each of the four 12-bit head/carry halves",
            NAMES[2]: "Previous four zero tests plus low bit and bit parity of every half",
            NAMES[3]: "Any GF(2) affine function of all48 head/carry bits and four half-zero indicators, with independently chosen coefficients per public node",
        },
        "results": {},
    }
    completed = 0
    observations = []
    physical_inputs = {}
    seen = {name: {} for name in NAMES[:3]}
    affine_bases = defaultdict(dict)
    try:
        Physical = load("rolling_screen_physical_reference", physical_path)
        Carry = load("rolling_screen_first3_reference", carry_path)
        assert "kickmix" not in sys.modules and "numpy" not in sys.modules
        fixture_rows = json.loads(fixture_path.read_text())
        # Only domain-admitted cutoff18 inputs. Round-robin weights so a
        # deterministic corpus prefix is not dominated by one error weight.
        groups = defaultdict(deque)
        for ordinal, row in enumerate(fixture_rows):
            if row["weight"] >= 18 and row["classification"]["admitted"]:
                groups[row["weight"]].append((ordinal, row))
        order = [32, 33, 30, 31, 28, 29, 26, 27, 24, 25, 22, 23, 20, 21, 18, 19, 34, 35]
        schedule = []
        while any(groups.values()):
            for weight in order:
                if groups[weight]:
                    schedule.append(groups[weight].popleft())
        report["eligible_physical_fixtures"] = len(schedule)
        tree = ast.parse(carry_path.read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "changed_carry")
        capture_lines = [n.lineno for n in ast.walk(fn)
                         if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name)
                         and n.value.id == "numerator" and len(n.targets) == 1
                         and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "carry"]
        assert len(capture_lines) == 1
        capture_line = capture_lines[0]
        report["observation_point"] = {
            "reference": str(carry_path.relative_to(root)),
            "function": "changed_carry",
            "line": capture_line,
            "meaning": "After exact head and flag assertions, before carry=numerator; current numerator is the post-update unit carry",
        }
        target_code = Carry.changed_carry.__code__

        def observe_row(node, head, carry, flag, input_id):
            assert 18 <= node < 35 and carry
            oid = len(observations)
            row = dict(observation_id=oid, input_id=input_id, node=node,
                       head=head, carry=carry, flag=flag)
            observations.append(row)
            for name in NAMES[:3]:
                if name in report["results"]:
                    continue
                key = features(name, node, head, carry)
                previous = seen[name].get(key)
                if previous is None:
                    seen[name][key] = oid
                elif observations[previous]["flag"] != flag:
                    report["results"][name] = {
                        "status": "REFUTED_BY_IDENTICAL_OBSERVATION",
                        "feature_tuple": list(key),
                        "observations": [observations[previous], row],
                    }
            name = NAMES[3]
            if name not in report["results"]:
                x, y, support = affine_features(head, carry), flag, 1 << oid
                basis = affine_bases[node]
                while x:
                    pivot = x.bit_length() - 1
                    if pivot not in basis:
                        basis[pivot] = (x, y, support)
                        break
                    bx, by, bs = basis[pivot]
                    x, y, support = x ^ bx, y ^ by, support ^ bs
                if not x and y:
                    ids = [j for j in range(len(observations)) if support >> j & 1]
                    xs = ys = 0
                    for j in ids:
                        item = observations[j]
                        assert item["node"] == node
                        xs ^= affine_features(item["head"], item["carry"])
                        ys ^= item["flag"]
                    assert xs == 0 and ys == 1
                    report["results"][name] = {
                        "status": "REFUTED_BY_GF2_INCONSISTENCY",
                        "node": node,
                        "proof": "XOR of feature vectors is0 while XOR of required flags is1; therefore no affine coefficients satisfy these rows",
                        "xor_features": xs, "xor_flags": ys,
                        "observations": [observations[j] for j in ids],
                    }

        for input_id, source in schedule[:report["max_trajectories"]]:
            old = source["boundary_oracle"]
            # Rebuild physical inputs independently; do not accept supplied
            # head/flag values merely because they appear in a fixture.
            fresh = Physical.boundary(source["roots"], source["values"], j_min=18)
            for key in ("raw_queries", "heads", "tail_flags", "terminal_unit"):
                assert fresh[key] == old[key], (input_id, key)
            classified = Physical.R.classify(source["roots"], source["values"])
            assert classified["reason_mask"] == 0
            captured = []
            def local_trace(frame, event, arg):
                if event == "line" and frame.f_lineno == capture_line:
                    v = frame.f_locals
                    if v["i"] >= 18:
                        captured.append((v["i"], v["heads"][v["i"]],
                                         v["numerator"], v["flag"]))
                return local_trace
            def global_trace(frame, event, arg):
                return local_trace if event == "call" and frame.f_code is target_code else None
            try:
                sys.settrace(global_trace)
                carry, seam = Carry.changed_carry(fresh)
            finally:
                sys.settrace(None)
            assert len(captured) == 17 and carry == captured[-1][2]
            assert carry == old["raw_carry"]
            physical_inputs[input_id] = {
                "input_id": input_id, "fixture_label": source["label"],
                "weight": source["weight"], "roots": source["roots"],
                "magnitudes": source["values"], "exact_reason_mask": classified["reason_mask"],
                "oracle_heads_flags_raw_rebuilt_and_matched": True,
            }
            for node, head, state_carry, flag in captured:
                observe_row(node, head, state_carry, flag, input_id)
            completed += 1
            if len(report["results"]) == len(NAMES):
                report["status"] = "ALL_FOUR_DECODER_FAMILIES_REFUTED"
                report["stop_reason"] = "Concrete counterexamples suffice; stopped early"
                break
        else:
            report["status"] = "BOUNDED_SCREEN_COMPLETE"
            report["stop_reason"] = "Eligible corpus or trajectory cap exhausted"
    except TimeoutError as exc:
        report["status"] = "BOUNDED_SCREEN_TIME_LIMIT"
        report["stop_reason"] = str(exc)
    except Exception as exc:
        report["status"] = "REFERENCE_INTEGRATION_BLOCKED"
        report["stop_reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        sys.settrace(None)
        signal.setitimer(signal.ITIMER_REAL, 0)
        for name in NAMES:
            report["results"].setdefault(name, {
                "status": "NOT_REFUTED_WITHIN_THIS_SCREEN",
                "no_correctness_claim": True,
            })
        required = {row["input_id"] for result in report["results"].values()
                    for row in result.get("observations", [])}
        report["counterexample_inputs"] = [physical_inputs[j] for j in sorted(required)]
        report["completed_trajectories"] = completed
        report["observed_node_states"] = len(observations)
        report["elapsed_seconds"] = time.monotonic() - started
        report["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report["reference_files_unchanged"] = all(digest(root/p) == value for p, value in before.items())
        report["limitations"] = [
            "This disproves only the listed decoder families at the observed boundary.",
            "No impossibility result for other nonlinear witnesses, extra retained data or a redesigned schedule.",
            "Curated fixtures are not independent distribution samples; no failure probability is estimated.",
            "The current production lineage is exercised, not a new official full-circuit verification.",
        ]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in (
            "status", "stop_reason", "completed_trajectories", "observed_node_states",
            "elapsed_seconds", "max_rss_kib", "reference_files_unchanged")}, indent=2))


if __name__ == "__main__":
    main()
