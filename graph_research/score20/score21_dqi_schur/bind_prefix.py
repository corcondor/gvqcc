"""Read-only source binding of old direct divisions to score19's e4 tape."""
import argparse
import json
from pathlib import Path

import kickmix as km

import score5_chem_width_classify as reference
import kmb_splice as splice
from bind import active_ranges
from outcome_dqi_chart_match import match


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("intervals", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(24, "source")
    target = builder.create_quantum_register(24, "target")
    import gf24_nested_norm
    import nested_norm_inverse
    # Selected binding used by public integration_v6/v7 verifier worker.
    reference.Direct.A = gf24_nested_norm
    reference.Direct.Prior = nested_norm_inverse
    reference.Direct.divide_deferred(builder, source, target)
    tape = builder.finish_circuit()
    template_path = args.out.with_suffix(".old.kmb")
    tape.to_file(template_path, format="kmb")
    template = splice.open_circuit(template_path)
    whole = splice.open_circuit(args.base, args.profile)
    pattern = template.opcodes
    original = list(template.operations(0,len(pattern)))
    options = {"modeled_core_Toffoli": tape.operation_statistics().num_toffoli_like,
               "component_qubits": tape.num_qubits,
               "component_operations": len(pattern),
               "scope": "nested source binding; exact whole contiguous old operation template, through injective wire renaming",
               "source_module": str(reference.Direct.__file__),
               "input_sha256": whole.profile["raw_kmb_sha256"],
               "opcode_matches": 0, "matched": []}
    positions = list(active_ranges(args.intervals, 889))
    cursor = 0
    while (start := whole.opcodes.find(pattern, cursor)) >= 0:
        end = start+len(pattern)
        cursor = start+1
        options["opcode_matches"] += 1
        mapping = match(original, whole.operations(start,end))
        if mapping is None:
            continue
        q = mapping["qubits"]
        source_slot = next((slot for slot in range(35)
                            if sorted(q[i] for i in range(24)) == list(range(slot*24,slot*24+24))),
                           None)
        high_q = sum(max(0,min(end,b)-max(start,a)) for a,b in positions if a < end and b > start)
        options["matched"].append(dict(start=start,end=end,source_slot=source_slot,
                       target_is_carry=sorted(q[i] for i in range(24,48)) == list(range(840,864)),
                       positions_at_Q889=high_q))
    options["exact_matches"] = len(options["matched"])
    options["exact_matches_with_Q889"] = sum(bool(x["positions_at_Q889"]) for x in options["matched"])
    options["covered_Q889_positions"] = sum(x["positions_at_Q889"] for x in options["matched"])
    args.out.write_text(json.dumps(options,indent=2)+"\n")
    print(json.dumps({k:v for k,v in options.items() if k!="matched"}))
    whole.close()
    template.close()


if __name__ == "__main__":
    main()
