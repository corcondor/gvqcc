#!/usr/bin/env python3
"""A scoped lower bound for phase-only invsqrt redesigns.

Assumes the basis-state/monomial model: each generic rotation contributes
alpha times a Boolean predicate, while all Clifford/T phases lie on the
one-eighth-turn grid. Does not claim a bound on arbitrary interferometric
circuits, other cost models, or changed arithmetic/qubit costs.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    maximum=3133452;first=65;epsilon=Fraction(1,1<<24)
    # These exact squared inequalities prove all allowed intervals are
    # disjoint and lie strictly inside (0, 1/8) turns.
    adjacent_gap=(1-epsilon)**2-4*epsilon*(maximum-1)
    upper_gap=Fraction(first)-(1+epsilon)**2*64
    assert adjacent_gap>0 and upper_gap>0
    count=maximum-first+1;k=(count-1).bit_length();assert k==22
    tol_upper=float(epsilon)/math.sqrt(maximum)
    arithmetic=1478.7506100300882;q=46;incumbent=78673.55534364567
    lower_rot=k*(.56*math.log2(k/(math.pi*tol_upper))+5.3)/4
    lower_cost=q*(arithmetic+lower_rot)
    target_cost=incumbent*(27.324751494620457/28)**3
    record={
        'status':'PASS_SCOPED_PHASE_ONLY_BOUND','domain_maximum':maximum,'domain_first_for_count':first,
        'relative_tolerance':str(epsilon),'disjoint_interval_exact_positive_gap':str(adjacent_gap),
        'all_intervals_below_one_eighth_exact_positive_gap':str(upper_gap),
        'distinct_required_phase_intervals':count,'minimum_generic_rotations':k,
        'argument':'For any fixed generic-predicate bit pattern, changing Clifford/T predicates shifts phase only by multiples of 1/8 turn. Hence there is at most one phase in (0,1/8) per generic pattern. The required disjoint intervals number more than 2^21, so at least 22 generic predicates are necessary.',
        'arithmetic_cost_assumed_unchanged':arithmetic,'qubits_assumed_unchanged':q,
        'maximum_possible_margin_turns_upper_bound':tol_upper,
        'ideal_22_rotation_toffoli_equivalent_lower_bound':lower_rot,
        'ideal_phase_only_cost_lower_bound':lower_cost,
        'incumbent_cost':incumbent,'maximum_phase_only_reduction_percent':100*(incumbent-lower_cost)/incumbent,
        'cost_needed_if_only_this_component_reaches_portfolio28':target_cost,
        'phase_only_can_reach28_under_assumptions':lower_cost<=target_cost,
        'scope':'Boolean-predicate monomial phase model with a fixed measurement transcript; Clifford/T phases on the 1/8-turn lattice. Unchanged Q46 and arithmetic mean used for cost comparison. No claim of a global optimum or impossibility of arithmetic, width, new interferometric, or multi-component improvements.',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    }
    a.out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':main()
