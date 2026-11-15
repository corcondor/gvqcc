#!/usr/bin/env python3
"""Sparse, phase-correct changes to the 4033-CCX ANGLE loader family.

The original family is only assumed correct on its two specified endpoint
subspaces. A tag-changing edit uses D^-1 F D, where an address-controlled
invertible affine D maps BOTH new endpoints to the original endpoints.
Tag-preserving edits can use a cheaper differential XOR; the mandatory exact
proof, rather than an arbitrary-target assumption, accepts each resulting family.

All output files are new. No physical chemistry accuracy or score claim follows
from a successful loader proof. CCX is reported in Toffoli units, not T gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOADERS = ROOT / "dqi_inputs/chemistry_4033"
DEFAULT_TABLE = DEFAULT_LOADERS / "submission_asterios_full.npz"
NUM_ADDRESSES, NUM_ANGLES, BATCH_SIZE, BROT = 1220, 75, 5, 8
EXPECTED_REGISTERS = {"selection": list(range(11)), **{
    f"word_{j}": list(range(11+8*j, 19+8*j)) for j in range(5)}}
TAG_MASK = sum((1 << (8*j+6)) | (1 << (8*j+7)) for j in range(5))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def set_bits(value):
    value = int(value)
    while value:
        bit = value & -value
        yield bit.bit_length() - 1
        value ^= bit


def parity(value):
    return int(value).bit_count() & 1


def pack_words(row):
    return sum(int(value) << (8*j) for j, value in enumerate(row))


def tag_delta(value):
    return tuple(((int(value) >> (8*j+6)) ^ (int(value) >> (8*j+7))) & 1
                 for j in range(5))


def validate_words(words):
    words = np.asarray(words)
    if words.shape != (NUM_ADDRESSES, NUM_ANGLES):
        raise ValueError("angle_words must have shape (1220,75)")
    if not np.issubdtype(words.dtype, np.integer) or np.any(words < 0) or np.any(words > 255):
        raise ValueError("angle_words must be 8-bit nonnegative integers")
    return words


def apply_changes(words, changes):
    """Apply unique {address,column,value[,old]} or {address,column,delta} edits."""
    original = validate_words(words)
    changed = original.copy()
    normalized, seen = [], set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("Each change must be an object")
        if set(change) - {"address", "column", "value", "delta", "old"}:
            raise ValueError("Unknown change fields")
        for key in ("address", "column"):
            if not isinstance(change.get(key), (int, np.integer)) or isinstance(change[key], bool):
                raise ValueError(f"{key} must be an integer")
        address, column = int(change["address"]), int(change["column"])
        if not 0 <= address < NUM_ADDRESSES or not 0 <= column < NUM_ANGLES:
            raise ValueError("Change outside the pinned table")
        if (address, column) in seen:
            raise ValueError("Duplicate word edit")
        seen.add((address, column))
        old = int(original[address, column])
        if "old" in change and int(change["old"]) != old:
            raise ValueError("Old-word guard mismatch")
        if ("value" in change) == ("delta" in change):
            raise ValueError("Specify exactly one of value or delta")
        field = "value" if "value" in change else "delta"
        if not isinstance(change[field], (int, np.integer)) or isinstance(change[field], bool):
            raise ValueError(f"{field} must be an integer")
        value = int(change[field]) if field == "value" else old + int(change[field])
        if not 0 <= value <= 255:
            raise ValueError("Changed word outside [0,255]; no implicit wraparound")
        changed[address, column] = value
        if value != old:
            xor = old ^ value
            normalized.append(dict(address=address, column=column, old=old,
                                   value=value, delta=value-old, xor=xor,
                                   tag_changed=bool(((xor >> 6) ^ (xor >> 7)) & 1)))
    return changed, sorted(normalized, key=lambda row: (row["address"], row["column"]))


def best_trie_order(addresses):
    """Exact minimum CCX count among shared tries with one global bit order.

    A depth-one literal is free. Every distinct prefix of depth >=2 is one
    temporary AND. The prefix partition depends only on the chosen bit subset,
    so a 2^11-subset dynamic program searches all 11! global variable orders.
    This is not a global Boolean circuit optimality claim.
    """
    addresses = tuple(sorted(set(map(int, addresses))))
    if not addresses:
        return tuple(range(10, -1, -1)), 0
    if any(a < 0 or a >= 2048 for a in addresses):
        raise ValueError("11-bit addresses required")
    full = 2047
    cost = [10**12] * 2048
    previous = [None] * 2048
    cost[0] = 0
    for mask in range(2048):
        for bit in range(10, -1, -1):
            if mask >> bit & 1:
                continue
            next_mask = mask | (1 << bit)
            add = len({a & next_mask for a in addresses}) if next_mask.bit_count() >= 2 else 0
            candidate = cost[mask] + add
            if candidate < cost[next_mask]:
                cost[next_mask] = candidate
                previous[next_mask] = (mask, bit)
    order, mask = [], full
    while mask:
        mask, bit = previous[mask]
        order.append(bit)
    return tuple(reversed(order)), int(cost[full])


def conjugation_adapter(old_previous, old_current, new_previous, new_current):
    """Return D(v)=v+w*(l(v)+c)+t mapping new endpoints to old ones.

    l(d)=l(d')=1 implies l(w)=0, so the shear is an involution. D^-1 is
    the same translation and shear in the opposite order.
    """
    x, y, xp, yp = map(int, (old_previous, old_current, new_previous, new_current))
    d, dp, t = x ^ y, xp ^ yp, xp ^ x
    w = d ^ dp
    if not w:
        return dict(kind="adapter", translation=t, shear=0, linear=0, offset=0)
    if not d or not dp:
        raise ValueError("Cannot conjugate coincident and distinct endpoint pairs")
    common = d & dp
    linear = common & -common if common else (d & -d) | (dp & -dp)
    assert parity(linear & d) == parity(linear & dp) == 1
    assert parity(linear & w) == 0
    offset = parity(linear & xp)
    operation = dict(kind="adapter", translation=t, shear=w, linear=linear, offset=offset)
    def apply(v):
        return v ^ (w if parity(v & linear) ^ offset else 0) ^ t
    assert apply(xp) == x and apply(yp) == y
    return operation


def family_operations(old, new, *, force_conjugation=False):
    old, new = validate_words(old), validate_words(new)
    operations = []
    for k in range(15):
        previous_old = old[:, 5*(k-1):5*k] if k else np.zeros((1220,5), dtype=np.uint64)
        previous_new = new[:, 5*(k-1):5*k] if k else np.zeros((1220,5), dtype=np.uint64)
        current_old, current_new = old[:,5*k:5*(k+1)], new[:,5*k:5*(k+1)]
        addresses = np.flatnonzero(np.any(previous_old != previous_new, axis=1)
                                   | np.any(current_old != current_new, axis=1))
        pre, post, descriptions = {}, {}, []
        for address in map(int, addresses):
            x, y, xp, yp = (pack_words(table[address]) for table in
                             (previous_old, current_old, previous_new, current_new))
            delta_previous, delta_current = x ^ xp, y ^ yp
            if not force_conjugation and not any(tag_delta(delta_previous)) and not any(tag_delta(delta_current)):
                differential = delta_previous ^ delta_current
                if differential:
                    post[address] = dict(kind="xor", mask=differential)
                mode = "tag_preserving_differential_exact_proof_required"
            else:
                adapter = conjugation_adapter(x, y, xp, yp)
                if adapter["translation"] or adapter["shear"]:
                    pre[address] = dict(adapter, inverse=False)
                    post[address] = dict(adapter, inverse=True)
                mode = "two_endpoint_affine_conjugation"
            descriptions.append(dict(address=address, mode=mode,
                                     delta_previous=delta_previous, delta_current=delta_current))
        operations.append(dict(batch=k, pre=pre, post=post, addresses=descriptions))
    return operations


def emit_sparse_operations(operations, *, classical_bit=1):
    """Emit one shared address trie, with phase-correct measurement cleanup.

    q51..q60 hold address-prefix ANDs; q61 holds a linear output predicate;
    q62 holds its product with the address predicate. All start/end at zero.
    The prefix at depth one is an address literal, costing no CCX.
    """
    if not operations:
        return [], dict(addresses=0, trie_ccx=0, shear_ccx=0, total_ccx=0,
                        variable_order=[], maximum_patch_scratch=0)
    order, trie_cost = best_trie_order(operations)
    lines, shear_count = [], 0
    def fanout(control, mask):
        for bit in set_bits(mask):
            lines.append(f"CX q{control} q{11+bit}")
    def leaf(address, predicate):
        nonlocal shear_count
        op = operations[address]
        if op["kind"] == "xor":
            fanout(predicate, op["mask"])
            return
        if op.get("inverse", False):
            fanout(predicate, op["translation"])
        if op["shear"]:
            # The shear leaves l(v) unchanged because l(w)=0.
            linear_lines = [f"CX q{11+bit} q61" for bit in set_bits(op["linear"])]
            if op["offset"]:
                linear_lines.append("X q61")
            lines.extend(linear_lines)
            lines.append(f"CCX q{predicate} q61 q62")
            shear_count += 1
            fanout(62, op["shear"])
            lines.extend([f"HMR q62 b{classical_bit}",
                          f"CZ q{predicate} q61 if b{classical_bit}"])
            lines.extend(reversed(linear_lines))
        if not op.get("inverse", False):
            fanout(predicate, op["translation"])
    def walk(depth, addresses, parent=None):
        bit = order[depth]
        for value in (0, 1):
            selected = [a for a in addresses if (a >> bit) & 1 == value]
            if not selected:
                continue
            if value == 0:
                lines.append(f"X q{bit}")
            if depth == 0:
                predicate = bit
            else:
                predicate = 50 + depth
                lines.append(f"CCX q{parent} q{bit} q{predicate}")
            if depth == 10:
                assert len(selected) == 1
                leaf(selected[0], predicate)
            else:
                walk(depth+1, selected, predicate)
            if depth:
                lines.extend([f"HMR q{predicate} b{classical_bit}",
                              f"CZ q{parent} q{bit} if b{classical_bit}"])
            if value == 0:
                lines.append(f"X q{bit}")
    walk(0, sorted(operations))
    assert sum(line.startswith("CCX ") for line in lines) == trie_cost + shear_count
    return lines, dict(addresses=len(operations), trie_ccx=trie_cost, shear_ccx=shear_count,
                       total_ccx=trie_cost+shear_count, variable_order=list(order),
                       maximum_patch_scratch=12 if shear_count else 10)


def estimate_family(old, new, *, force_conjugation=False, feature_patches=False):
    """Pure-numpy cost estimate; no kickmix import or mutation."""
    rows = []
    for row in family_operations(old, new, force_conjugation=force_conjugation):
        feature = dict(added_ccx=0, addresses=0)
        post_operations = row["post"]
        if feature_patches and row["batch"]:
            from score2_angle_feature_patch import estimate_feature_xors
            feature_masks = {a:op["mask"] for a,op in post_operations.items() if op["kind"] == "xor"}
            feature = estimate_feature_xors(feature_masks)
            post_operations = {a:op for a,op in post_operations.items() if op["kind"] != "xor"}
        _, pre = emit_sparse_operations(row["pre"])
        _, post = emit_sparse_operations(post_operations)
        rows.append(dict(batch=row["batch"], pre=pre, post=post,
                         feature=feature,
                         added_ccx_per_pass=pre["total_ccx"]+post["total_ccx"]+feature["added_ccx"],
                         addresses=row["addresses"]))
    total = sum(row["added_ccx_per_pass"] for row in rows)
    return dict(added_ccx_per_pass=total, added_official_toffoli_both_passes=2*total,
                maximum_loader_qubits=128, chemistry_accuracy_tested=False,
                loader_exact_proof_run=False, score_improvement_claimed=False, loaders=rows)


def build_sparse_family(changes, *, source_dir=DEFAULT_LOADERS, table_path=DEFAULT_TABLE,
                        output_dir=None, native_seeds=(), force_conjugation=False,
                        feature_patches=False):
    import kickmix as km
    from chemistry_reachable_exact_proof import pack, prove_one
    started = time.monotonic()
    source_dir, table_path = Path(source_dir), Path(table_path)
    if output_dir is not None and Path(output_dir).exists():
        raise FileExistsError("Use a new output directory")
    with np.load(table_path, allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
    old = validate_words(data["angle_words"])
    if data["W"].shape[:2] != (8,143) or data["U"].shape[-1] != 76:
        raise ValueError("Pinned R8/B143/N76 layout required")
    new, changes = apply_changes(old, changes)
    operations = family_operations(old, new, force_conjugation=force_conjugation)
    addresses = np.arange(1220, dtype=np.uint64)
    address_bits = [pack((addresses >> bit) & 1) for bit in range(11)]
    zero = np.zeros((1220,5), dtype=np.uint64)
    circuits, sources, rows, checks = [], [], [], []
    for k, operation in enumerate(operations):
        path = source_dir / f"angle_k_{k}.kmb"
        raw = path.read_bytes()
        source = km.Circuit.from_file(path)
        registers = {name: [int(str(q)[1:]) for q in qs] for name, qs in source.register_data.items()}
        if registers != EXPECTED_REGISTERS:
            raise ValueError(f"Unexpected register mapping at batch {k}")
        if source.num_qubits > 128 or source.num_qubits < 63:
            raise ValueError("Insufficient existing scratch or 128-qubit cap exceeded")
        candidate = source
        feature = dict(added_ccx=0, addresses=0)
        post_operations = operation["post"]
        if feature_patches and k:
            from score2_angle_feature_patch import insert_feature_xors
            feature_masks = {a:op["mask"] for a,op in post_operations.items() if op["kind"] == "xor"}
            candidate, feature = insert_feature_xors(candidate, feature_masks, classical_bit=source.num_bits)
            post_operations = {a:op for a,op in post_operations.items() if op["kind"] != "xor"}
        pre_lines, pre = emit_sparse_operations(operation["pre"], classical_bit=source.num_bits)
        post_lines, post = emit_sparse_operations(post_operations, classical_bit=source.num_bits)
        if pre_lines:
            candidate = km.Circuit("\n".join(pre_lines)+"\n") + candidate
        if post_lines:
            candidate = candidate + km.Circuit("\n".join(post_lines)+"\n")
        if candidate.register_data != source.register_data:
            raise AssertionError("Register metadata changed")
        if candidate.num_qubits > 128 or (not feature_patches and candidate.num_qubits != source.num_qubits):
            raise AssertionError("Loader qubit cap changed")
        before = int(source.operation_statistics().num_toffoli_like)
        after = int(candidate.operation_statistics().num_toffoli_like)
        addition = pre["total_ccx"] + post["total_ccx"] + feature["added_ccx"]
        if after != before + addition:
            raise AssertionError("Toffoli accounting mismatch")
        previous = new[:,5*(k-1):5*k].astype(np.uint64) if k else zero
        current = new[:,5*k:5*(k+1)].astype(np.uint64)
        for direction, incoming, expected in (("forward", previous, current), ("reverse", current, previous)):
            checks.append(prove_one(candidate, incoming, expected, address_bits, f"k={k}/{direction}"))
        rows.append(dict(batch=k, source_sha256=hashlib.sha256(raw).hexdigest(),
                         source_ops=len(source), patched_ops=len(candidate), num_qubits=candidate.num_qubits,
                         source_num_qubits=source.num_qubits,
                         source_classical_bits=source.num_bits, patched_classical_bits=candidate.num_bits,
                         source_ccx=before, patched_ccx=after, added_ccx_per_pass=addition,
                         pre=pre, post=post, feature=feature, modified_addresses=operation["addresses"]))
        circuits.append(candidate)
        sources.append(raw)
    source_total = sum(row["source_ccx"] for row in rows)
    total = sum(row["patched_ccx"] for row in rows)
    if source_total != 4033:
        raise AssertionError(("Expected 4033-Toffoli source family", source_total))
    native = []
    if native_seeds:
        import sys
        sys.path.insert(0, str(ROOT / "official_sources/Inzainos/verifiers"))
        from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
        for seed in native_seeds:
            recovered, layout, measured = recover_words_from_circuits(
                circuits, num_vectors=1220, num_angles=75, shots_per_address=1, seed=int(seed))
            if not np.array_equal(recovered, new) or measured != 2*total:
                raise AssertionError("Official native recovery mismatch")
            native.append(dict(seed=int(seed), addresses=1220, shots_per_address=1,
                               forward_and_reverse=True, measured_toffoli=measured,
                               status="PASS_LOADER_ONLY"))
    report = dict(status="EXACT_SPARSE_PATCH_REACHABLE_PASS", changes=changes,
                  source_table_sha256=sha256(table_path), source_ccx_per_pass=source_total,
                  candidate_ccx_per_pass=total, added_ccx_per_pass=total-source_total,
                  added_official_toffoli_both_passes=2*(total-source_total),
                  candidate_official_angle_toffoli_both_passes=2*total,
                  max_loader_qubits=max(c.num_qubits for c in circuits),
                  tag_contract="Exact both-endpoint proof; arbitrary-target source XOR not assumed",
                  boundary_oracle_address_domain=2048, family_address_domain=1220,
                  feature_patch_address_domain=1220 if feature_patches else None,
                  address_transition_cases=1220*15*2,
                  all_HMR_measurement_branches_covered=True,
                  HMR_formal_variables_cancelled=sum(r["HMR_formal_variables_cancelled"] for r in checks),
                  first_forward_input_and_last_reverse_output_zero=True,
                  source_circuits_preserved_inside_adapters=not feature_patches,
                  source_gate_sequence_preserved=True,
                  other_factorization_arrays_preserved=True,
                  full_competition_shots_run=False, chemistry_physical_accuracy_tested=False,
                  score_improvement_claimed=False, checks=checks, loaders=rows,
                  native_checks=native, force_conjugation=force_conjugation,
                  feature_patches=feature_patches,
                  builder_sha256=sha256(__file__),
                  proof_engine_sha256=sha256(Path(__file__).with_name("chemistry_reachable_exact_proof.py")),
                  seconds=time.monotonic()-started)
    if feature_patches:
        report["feature_builder_sha256"] = sha256(Path(__file__).with_name("score2_angle_feature_patch.py"))
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True)
        for k, (circuit, raw, row) in enumerate(zip(circuits, sources, rows)):
            destination = output_dir / f"angle_k_{k}.kmb"
            if row["pre"]["addresses"] or row["post"]["addresses"] or row["feature"]["addresses"]:
                circuit.to_file(destination, format="kmb")
            else:
                destination.write_bytes(raw)
            restored = km.Circuit.from_file(destination)
            if str(restored) != str(circuit) or restored.register_data != circuit.register_data:
                raise AssertionError("Serialized loader differs from the proved circuit")
            row["candidate_sha256"] = sha256(destination)
        updated = dict(data)
        updated["angle_words"] = new
        destination = output_dir / "submission.npz"
        np.savez_compressed(destination, **updated)
        with np.load(destination, allow_pickle=False) as restored:
            if set(restored.files) != set(updated) or any(
                    restored[key].dtype != updated[key].dtype or
                    not np.array_equal(restored[key], updated[key]) for key in updated):
                raise AssertionError("Serialized factorization differs from proved arrays")
        report["serialized_candidate_gate_sequences_verified"] = True
        report["serialized_factorization_arrays_verified"] = True
        report["candidate_table_sha256"] = sha256(destination)
        (output_dir / "changes.json").write_text(json.dumps(changes, indent=2)+"\n")
        (output_dir / "proof.json").write_text(json.dumps(report, indent=2)+"\n")
    return circuits, new, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changes", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_LOADERS)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--estimate-only", action="store_true")
    parser.add_argument("--force-conjugation", action="store_true")
    parser.add_argument("--feature-patches", action="store_true",
                        help="Use valid-domain existing features for cheaper tag-preserving deltas in batches1..14")
    parser.add_argument("--native-seeds", default="20261115,20261116")
    args = parser.parse_args()
    changes = json.loads(args.changes.read_text())
    if isinstance(changes, dict):
        changes = changes["changes"]
    if args.estimate_only:
        with np.load(args.table, allow_pickle=False) as archive:
            old = archive["angle_words"]
        new, normalized = apply_changes(old, changes)
        report = estimate_family(old, new, force_conjugation=args.force_conjugation,
                                 feature_patches=args.feature_patches)
        report["changes"] = normalized
    else:
        if args.out is None:
            parser.error("--out is required unless --estimate-only")
        _, _, report = build_sparse_family(changes, source_dir=args.source_dir,
                    table_path=args.table, output_dir=args.out,
                    native_seeds=tuple(int(s) for s in args.native_seeds.split(",") if s),
                    force_conjugation=args.force_conjugation,
                    feature_patches=args.feature_patches)
    print(json.dumps({key:value for key,value in report.items() if key not in {"checks", "loaders"}}, indent=2))


if __name__ == "__main__":
    main()
