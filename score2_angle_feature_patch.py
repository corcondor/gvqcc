#!/usr/bin/env python3
"""Insert sparse, tag-preserving deltas into an existing ANGLE feature stage.

The exact scope is valid addresses 0..1219 with the canonical five input tags.
At the insertion point the existing control span has high-address rank 76/77
and low-address rank 16/16. A high point in the span is free. Otherwise a
codimension-one identity represents it as one product of two free functions.
Each independent output direction then costs one CCX with a free low function.
Measurement cleanup restores the extra helper without another Toffoli.
"""
from __future__ import annotations

from collections import defaultdict

from score2_angle_sparse_patch import set_bits


# Exact valid-domain profile; the builder recomputes and checks it for every
# modified source circuit. This list is used only for pure-numpy cost previews.
BASELINE_MISSING_HIGH = (0,5,6,7,13,14,15,16,17,19,21,22,23,24,28,30,32,33,
                        34,35,36,39,41,43,44,45,46,48,49,51,52,55,57,58,66,
                        67,68,70,71,72,73,74,75,76)


def vector_basis(vectors):
    """Highest-pivot GF(2) basis, preserving coefficients in the input list."""
    basis = {}
    for index, value in enumerate(vectors):
        value, coefficients = int(value), 1 << index
        while value:
            pivot = value.bit_length()-1
            if pivot not in basis:
                basis[pivot] = value, coefficients
                break
            row, combination = basis[pivot]
            value ^= row
            coefficients ^= combination
    return basis


def solve(basis, value):
    value, coefficients = int(value), 0
    while value:
        pivot = value.bit_length()-1
        if pivot not in basis:
            return None
        row, combination = basis[pivot]
        value ^= row
        coefficients ^= combination
    return coefficients


def xor_selected(values, selection):
    result = 0
    for index in set_bits(selection):
        result ^= values[index]
    return result


def feature_context(circuit):
    """Exact feature truth tables, plus independence from all 35 data bits."""
    from chemistry_joint_product_resynthesis import extract, DATA, TAGS
    from chemistry_affine_span_resynthesis import parse_line
    extraction = extract(circuit)
    count, ones = 1220, (1 << 1220)-1
    state = [0] * circuit.num_qubits
    dependence = [0] * circuit.num_qubits
    for bit in range(11):
        state[bit] = sum(1 << address for address in range(count) if address >> bit & 1)
    for index, qubit in enumerate(DATA):
        dependence[qubit] = 1 << index
    for tag, (left, right) in zip(sorted(TAGS), [(0,1), (0,2), (1,2), (0,3), (1,3)]):
        state[tag] = state[left] & state[right]
        # Before the five opening CX gates, the public bit7 is tag XOR bit6.
        dependence[tag] = dependence[tag-1]
    for line in extraction["lines"][:extraction["first"]]:
        gate, qubits, condition = parse_line(line)
        if not gate or gate in {"REGISTER", "APPEND_TO_REGISTER"}:
            continue
        if condition is not None:
            raise ValueError("Unexpected conditioned feature preparation")
        if gate == "X":
            state[qubits[0]] ^= ones
        elif gate == "CX":
            left, target = qubits
            state[target] ^= state[left]
            dependence[target] ^= dependence[left]
        elif gate == "CCX":
            left, right, target = qubits
            if dependence[left] or dependence[right]:
                raise ValueError("Feature preparation reads an unconstrained data bit")
            state[target] ^= state[left] & state[right]
        elif gate == "R":
            if state[qubits[0]] or dependence[qubits[0]]:
                raise ValueError("Feature preparation resets an unknown wire")
        else:
            raise ValueError("Unsupported feature prefix: " + line)
    pool = extraction["pool"]
    if any(dependence[q] for q in pool):
        raise ValueError("Control pool depends on unconstrained data")
    functions = [state[q] for q in pool] + [ones]
    if len(vector_basis(functions)) != len(functions):
        raise ValueError("The physical feature coordinates are not independent")
    def group_space(group):
        constraint_basis, function_rows, physical_rows = {}, [], []
        for index, function in enumerate(functions):
            representative = sum(((function >> (address & ~15 if group == "high" else address & 15)) & 1)
                                 << address for address in range(count))
            constraint, physical = function ^ representative, 1 << index
            while constraint:
                pivot = constraint.bit_length()-1
                if pivot not in constraint_basis:
                    constraint_basis[pivot] = constraint, physical
                    break
                row, coefficient = constraint_basis[pivot]
                constraint ^= row
                physical ^= coefficient
            if not constraint:
                actual = xor_selected(functions, physical)
                points = 77 if group == "high" else 16
                compressed = sum(((actual >> (16*a if group == "high" else a)) & 1) << a
                                 for a in range(points))
                function_rows.append(compressed)
                physical_rows.append(physical)
        basis = vector_basis(function_rows)
        def expression(value):
            selection = solve(basis, value)
            return None if selection is None else xor_selected(physical_rows, selection)
        return dict(rank=len(basis), functions=function_rows, physical=physical_rows,
                    basis=basis, expression=expression)
    high, low = group_space("high"), group_space("low")
    if high["rank"] != 76 or low["rank"] != 16:
        raise ValueError(("Unexpected feature intersection ranks", high["rank"], low["rank"]))
    missing = [a for a in range(77) if high["expression"](1 << a) is None]
    # A one-dimensional annihilator makes this precisely its support.
    # Constant 1 and seven distinct address coordinates rule out support 1/2.
    if len(missing) < 4 or len(missing) % 2:
        raise ValueError("Unexpected codimension-one relation")
    if tuple(missing) != BASELINE_MISSING_HIGH:
        raise ValueError("Source feature profile differs from the pinned cost model")
    return dict(extraction=extraction, pool=pool, functions=functions, high=high,
                low=low, missing_high_points=missing, num_qubits=circuit.num_qubits,
                all_pool_functions_independent_of_data=True)


def estimate_feature_xors(address_masks):
    """Exact CCX count for the checked baseline profile, without native imports."""
    free_components, address_masks = split_free_feature_components(address_masks)
    groups = defaultdict(dict)
    for address, mask in address_masks.items():
        if mask:
            groups[int(address) >> 4][int(address) & 15] = int(mask)
    rows = []
    for h, masks in sorted(groups.items()):
        reference = masks.get(0, 0)
        differences = [masks.get(l, 0) ^ reference for l in range(4 if h == 76 else 16)]
        rows.append(dict(high_address=h, output_rank=len(vector_basis(differences)),
                         affine_constant_direction=hex(reference),
                         high_indicator_ccx=int(h in BASELINE_MISSING_HIGH)))
    for row in rows:
        row["added_ccx"] = row["output_rank"] + row["high_indicator_ccx"]
    return dict(added_ccx=sum(row["added_ccx"] for row in rows),
                addresses=len(address_masks), groups=rows,
                free_feature_components=len(free_components),
                profile="baseline4033; checked again by the circuit builder")


def in_baseline_feature_span(function):
    """Membership in A(high) XOR B(low), with one exact high parity relation."""
    high = [(function >> (16*h)) & 1 for h in range(77)]
    if sum(high[h] for h in BASELINE_MISSING_HIGH) & 1:
        return False
    low = [((function >> l) & 1) ^ high[0] for l in range(16)]
    return all(((function >> a) & 1) == (high[a >> 4] ^ low[a & 15]) for a in range(1220))


def split_free_feature_components(address_masks):
    """Extract individually free components of an output-rank decomposition.

    This includes arbitrary admissible high block combinations, not just one
    high block at a time. It does not claim optimal splitting for all tensors.
    """
    directions = []
    for mask in address_masks.values():
        if mask and solve(vector_basis(directions), mask) is None:
            directions.append(int(mask))
    basis = vector_basis(directions)
    functions = [0] * len(directions)
    for address, mask in address_masks.items():
        coefficients = solve(basis, mask)
        if coefficients is None:
            raise AssertionError("Output function decomposition failed")
        for index in set_bits(coefficients):
            functions[index] |= 1 << int(address)
    free = [(function, direction) for function, direction in zip(functions, directions)
            if in_baseline_feature_span(function)]
    residual = dict(address_masks)
    for function, direction in free:
        for address in set_bits(function):
            residual[address] ^= direction
    return free, {a:mask for a,mask in residual.items() if mask}


def backwards_output_direction(context, public_mask):
    """Pull a final public XOR through the suffix, rejecting nonlinear effects."""
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA
    error = int(public_mask) << 11
    extraction = context["extraction"]
    for line in reversed(extraction["lines"][extraction["first"]:]):
        gate, qubits, condition = parse_line(line)
        if not gate or gate in {"REGISTER", "APPEND_TO_REGISTER", "X"}:
            continue
        if gate == "CX":
            if condition is not None:
                raise ValueError("Conditioned data linear transform")
            left, target = qubits
            if error >> left & 1:
                error ^= 1 << target
        elif gate == "CCX":
            if any(error >> q & 1 for q in qubits[:2]):
                raise ValueError("Output delta reaches a nonlinear control")
        elif gate in {"HMR", "R", "CZ"}:
            if any(error >> q & 1 for q in qubits):
                raise ValueError("Output delta reaches a reset or phase control")
        else:
            raise ValueError("Unsupported suffix operation: " + line)
    if any(q not in DATA for q in set_bits(error)):
        raise ValueError("Tag-changing output delta cannot use this feature patch")
    return error


def prepare_forms(forms, pool):
    """Reversible in-place coordinates for one or two independent affine forms."""
    constant = 1 << len(pool)
    frame = [1 << index for index in range(len(pool))]
    lines, controls = [], []
    for form in forms:
        basis = vector_basis(frame + [constant])
        selected = solve(basis, form)
        if selected is None:
            raise ValueError("Affine form unavailable in current coordinates")
        indexes = [i for i in range(len(pool)) if selected >> i & 1]
        pivot = next((i for i in indexes if pool[i] not in controls), None)
        if pivot is None:
            raise ValueError("Dependent affine controls")
        target = pool[pivot]
        for index in indexes:
            if index != pivot:
                lines.append(f"CX q{pool[index]} q{target}")
                frame[pivot] ^= frame[index]
        if selected >> len(pool) & 1:
            lines.append(f"X q{target}")
            frame[pivot] ^= constant
        if frame[pivot] != form:
            raise AssertionError("Affine control coordinate mismatch")
        controls.append(target)
    return lines, controls


def output_product(left, right, direction):
    targets = list(set_bits(direction))
    if not targets:
        return []
    target = targets[0]
    if left in targets or right in targets or left == right:
        raise ValueError("Output/control alias")
    fanout = [f"CX q{target} q{other}" for other in targets[1:]]
    return fanout + [f"CCX q{left} q{right} q{target}"] + list(reversed(fanout))


def insert_feature_xors(circuit, address_masks, *, classical_bit):
    """Return a new circuit and exact-scoped construction certificate."""
    import kickmix as km
    if not address_masks:
        return circuit, dict(added_ccx=0, addresses=0, groups=[])
    context = feature_context(circuit)
    pool, high, low = context["pool"], context["high"], context["low"]
    helper = circuit.num_qubits
    if helper >= 128:
        raise ValueError("No free physical helper below the 128-qubit cap")
    original_addresses = len(address_masks)
    free_components, residual_masks = split_free_feature_components(address_masks)
    lines, free_rows = [], []
    feature_basis = vector_basis(context["functions"])
    for function, public_direction in free_components:
        form = solve(feature_basis, function)
        if form is None:
            raise AssertionError("Pure cost model and exact feature membership disagree")
        internal = backwards_output_direction(context, public_direction)
        if form == 1 << len(pool):
            lines.extend(f"X q{target}" for target in set_bits(internal))
        else:
            preparation, controls = prepare_forms([form], pool)
            lines += preparation + [f"CX q{controls[0]} q{target}" for target in set_bits(internal)] + list(reversed(preparation))
        free_rows.append(dict(address_weight=function.bit_count(), function=hex(function),
                              internal_direction=hex(internal), affine_form=hex(form)))
    by_high = defaultdict(dict)
    for address, mask in sorted(residual_masks.items()):
        if not 0 <= int(address) < 1220:
            raise ValueError("Feature patch is restricted to valid addresses")
        internal = backwards_output_direction(context, mask)
        if internal:
            by_high[int(address) >> 4][int(address) & 15] = internal
    groups, added = [], 0
    for h, low_masks in sorted(by_high.items()):
        # Rank-factor the 16-by-35 output table. Free low functions permit one
        # CCX for each independent output direction, shared across addresses.
        reference = low_masks.get(0, 0)
        differences = {l:low_masks.get(l, 0) ^ reference for l in range(4 if h == 76 else 16)}
        directions = []
        for direction in differences.values():
            if solve(vector_basis(directions), direction) is None:
                directions.append(direction)
        direction_basis = vector_basis(directions)
        selectors = [0] * len(directions)
        for l, direction in differences.items():
            coefficients = solve(direction_basis, direction)
            if coefficients is None:
                raise AssertionError("Output rank decomposition failed")
            for index in set_bits(coefficients):
                selectors[index] |= 1 << l
        high_form = high["expression"](1 << h)
        high_product = high_form is None
        factor_forms = None
        if high_product:
            alternatives = [a for a in context["missing_high_points"] if a != h]
            first, second = alternatives[:2]
            # Both two-point indicators lie in the same codimension-one kernel.
            u, v = (1 << h) | (1 << first), (1 << h) | (1 << second)
            assert u & v == 1 << h
            factor_forms = [high["expression"](u), high["expression"](v)]
            if any(form is None for form in factor_forms):
                raise AssertionError("Codimension-one factorization failed")
            preparation, controls = prepare_forms(factor_forms, pool)
            lines += preparation + [f"CCX q{controls[0]} q{controls[1]} q{helper}"] + list(reversed(preparation))
            added += 1
        if reference:
            if high_product:
                lines.extend(f"CX q{helper} q{target}" for target in set_bits(reference))
            else:
                preparation, controls = prepare_forms([high_form], pool)
                lines += preparation + [f"CX q{controls[0]} q{target}" for target in set_bits(reference)] + list(reversed(preparation))
        for selector, direction in zip(selectors, directions):
            low_form = low["expression"](selector)
            if low_form is None:
                raise AssertionError("Full low-address space missing a selector")
            if high_product:
                preparation, controls = prepare_forms([low_form], pool)
                left, right = helper, controls[0]
            else:
                preparation, controls = prepare_forms([high_form, low_form], pool)
                left, right = controls
            lines += preparation + output_product(left, right, direction) + list(reversed(preparation))
            added += 1
        if high_product:
            preparation, controls = prepare_forms(factor_forms, pool)
            lines += preparation + [f"HMR q{helper} b{classical_bit}",
                                    f"CZ q{controls[0]} q{controls[1]} if b{classical_bit}"] + list(reversed(preparation))
        groups.append(dict(high_address=h, low_addresses=sorted(low_masks),
                           high_indicator_ccx=int(high_product), output_rank=len(directions),
                           affine_constant_direction=hex(reference),
                           output_ccx=len(directions), added_ccx=len(directions)+int(high_product),
                           low_selectors=selectors,
                           internal_output_directions=[hex(d) for d in directions],
                           high_forms=[hex(f) for f in factor_forms] if high_product else [hex(high_form)]))
    extraction = context["extraction"]
    cut = extraction["first"]
    candidate = km.Circuit("\n".join(extraction["lines"][:cut]+lines+extraction["lines"][cut:])+"\n")
    if int(candidate.operation_statistics().num_toffoli_like - circuit.operation_statistics().num_toffoli_like) != added:
        raise AssertionError("Feature CCX accounting mismatch")
    return candidate, dict(status="CONSTRUCTION_REQUIRES_WHOLE_FAMILY_PROOF", added_ccx=added,
                           addresses=original_addresses, residual_addresses=len(residual_masks),
                           free_feature_components=free_rows, insertion_line=cut, patch_operations=len(lines),
                           source_qubits=circuit.num_qubits, candidate_qubits=candidate.num_qubits,
                           extra_helper=helper if any(g["high_indicator_ccx"] for g in groups) else None,
                           domain="1220 valid addresses with canonical five input tags",
                           high_function_rank=high["rank"], high_domain_size=77,
                           low_function_rank=low["rank"], low_domain_size=16,
                           missing_high_point_indicators=context["missing_high_points"],
                           output_data_independence_checked=True, groups=groups)
