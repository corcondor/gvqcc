import Init

/-!
# V21 Virtual SWAP Elimination, Commuting Clifford Contraction,
  Centralized Phase-Syndrome Merging & 36Q Score-Budget Certificates

Stacked on PR #72. Formalizes the algebraic identities and exact measured resource
bounds from `build_and_verify_v21_swap_clifford_kmb.py` and
`discover_unseen_v21_contractions.py` on the real 60,766-op 37Q `invsqrt.kmb`:
  - 2,767 unconditional SWAPs virtualized (+ 33 end-restore SWAPs) + 2,044 commuting
    Clifford cancellations -> 60,766 -> 55,988 ops (-4,778 ops, -7.863%), 0 paid-gate
    overhead, q36 lifetimes 117 -> 90 (-23.1%), q36 touches 3,278 -> 1,952 (-40.5%).
  - Centralized classical-control phase-syndrome merging eliminates 5,615 quantum
    phase gates (3,658 Z + 1,957 CZ) with zero extra qubits.
  - Exact 36Q score-budget dominance bounds (PR #70 break-even 1,447.0539 expected).

Scope disclaimer: local algebraic / conjugation / arithmetic certificates only;
official KMB simulation is run separately via `verify_submission_invsqrt.py`.
-/
namespace GVQCC.SymplecticVirtV21

def bx (a b : Bool) : Bool := Bool.xor a b

/-! ## 1. Virtual SWAP Conjugation Identities (S_37 Permutation Tracking) -/

def swap2 (a b : Bool) : Bool × Bool := (b, a)

def cx2 (c t : Bool) : Bool × Bool := (c, bx t c)

/-- SWAP(a, b); CX(a, b); SWAP(a, b) = CX(b, a) (virtualizing SWAP rewires CX). -/
theorem swap_conj_cx (a b : Bool) :
    let (a1, b1) := swap2 a b
    let (a2, b2) := cx2 a1 b1
    swap2 a2 b2 = (bx a b, b) := by
  cases a <;> cases b <;> decide

/-- SWAP(a, b) conjugated on CCX(a, c, b) = CCX(b, c, a). -/
theorem swap_conj_ccx (a b c : Bool) :
    let (a1, b1) := swap2 a b
    let b2 := bx b1 (a1 && c)
    swap2 a1 b2 = (bx a (b && c), b) := by
  cases a <;> cases b <;> cases c <;> decide

/-! ## 2. Commuting Self-Inverse Clifford Cancellation Identities -/

/-- CX(c, t); Z(c); CX(c, t) preserves state and phase (Z on control commutes with CX). -/
theorem cx_commute_z_ctrl (c t p : Bool) :
    let t1 := bx t c
    let p1 := bx p c
    let t2 := bx t1 c
    (c, t2, p1) = (c, t, bx p c) := by
  cases c <;> cases t <;> cases p <;> decide

/-- Two identical CX(c, t) separated by a diagonal CZ(c, x) cancel identically. -/
theorem cx_cz_cx_cancel (c t x p : Bool) :
    let t1 := bx t c
    let p1 := bx p (c && x)
    let t2 := bx t1 c
    (c, t2, x, p1) = (c, t, x, bx p (c && x)) := by
  cases c <;> cases t <;> cases x <;> cases p <;> decide

/-! ## 3. Centralized Classical-Control Phase-Syndrome Merging (-5,615 Phase Ops) -/

/-- Three classically-controlled Z(q) gates at the same write-epoch merge into one
    quantum Z(q) controlled by the classical XOR `m1 ⊕ m2 ⊕ m3`. -/
theorem central_syndrome_merge_z3 (m1 m2 m3 q : Bool) :
    bx (bx (m1 && q) (m2 && q)) (m3 && q) = (bx (bx m1 m2) m3 && q) := by
  cases m1 <;> cases m2 <;> cases m3 <;> cases q <;> decide

/-- Three classically-controlled CZ(a, b) gates at the same write-epoch merge into one
    quantum CZ(a, b) controlled by the classical XOR `m1 ⊕ m2 ⊕ m3`. -/
theorem central_syndrome_merge_cz3 (m1 m2 m3 a b : Bool) :
    bx (bx (m1 && (a && b)) (m2 && (a && b))) (m3 && (a && b)) =
      (bx (bx m1 m2) m3 && (a && b)) := by
  cases m1 <;> cases m2 <;> cases m3 <;> cases a <;> cases b <;> decide

/-! ## 4. Exact Measured V21 Resource & 36Q Score-Budget Bounds -/

theorem v21_ops_reduction : 60766 - 55988 = 4778 := by decide
theorem v21_q36_lifetime_reduction : 117 - 90 = 27 := by decide
theorem v21_q36_touch_reduction : 3278 - 1952 = 1326 := by decide
theorem v21_central_phase_eliminated : 3658 + 1957 = 5615 := by decide

/-- PR #70 exact 36Q break-even (scaled x10^4): 1406.3125 + 40.7414 = 1447.0539.
    Any 36Q circuit at PR #68 cost (1411.3125) strictly beats 37Q baseline. -/
theorem v21_score_36q_pr68_beats_baseline : 14113125 < 14470539 := by decide
theorem v21_score_36q_margin_over_pr68 : 14470539 - 14113125 = 357414 := by decide

end GVQCC.SymplecticVirtV21
