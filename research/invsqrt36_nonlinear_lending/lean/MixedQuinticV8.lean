import Std.Tactic.BVDecide

namespace GVQCC.V8

-- Exact Boolean phase identities for serialized V8 edits.
-- Source and candidate have identical reversible data scaffold.
-- Each guard is arbitrary, with no independence assumption.
theorem phase_29648 (q34 q15 q35 c270 c271 : Bool) :
    Bool.xor (c270 && q34)
      (c271 && Bool.xor q35 (q34 && !q15)) =
    Bool.xor (c271 && Bool.xor q35 (q34 && !q15))
      (c270 && q34) := by bv_decide

-- 8 native instructions -> 5. q22' = q22 XOR q20*q28 XOR q3.
theorem phase_41029 (q3 q17 q32 q20 q28 q22 c808 c113 : Bool) :
    Bool.xor (c808 && q17 && q32)
      (c113 && Bool.xor (Bool.xor q3 q20) (Bool.xor q22 (q20 && q28))) =
    Bool.xor (Bool.xor (c113 && q20)
      (c113 && Bool.xor (Bool.xor q22 (q20 && q28)) q3))
      (c808 && q17 && q32) := by bv_decide

-- Actual transposed classical/monomial guard matrix at [10189,10205).
-- Each u_i denotes the corresponding q21*q_i monomial.
theorem phase_10189 (u2 u3 u4 u5 u6 u11 u12 u14 g h j : Bool) :
    Bool.xor
      (Bool.xor (g && Bool.xor (Bool.xor (Bool.xor (Bool.xor u3 u4) u5) u6)
         (Bool.xor u11 u14))
        (h && Bool.xor (Bool.xor (Bool.xor u2 u4) u6) (Bool.xor u12 u14)))
      (j && Bool.xor (Bool.xor (Bool.xor u2 u4) u6) (Bool.xor u12 u14)) =
    Bool.xor
      (Bool.xor (g && Bool.xor (Bool.xor u3 u5) u11)
        ((Bool.xor (Bool.xor g h) j) && Bool.xor (Bool.xor u4 u6) u14))
      ((Bool.xor h j) && Bool.xor u2 u12) := by bv_decide

-- Nested two-clean-hub degree-five phase: measured uncompute of
-- h2=h1*c before h1=a*b, with independent measurement outcomes.
-- This is a local branch-phase law, not a full quantum channel proof.
theorem nested_quintic_phase (a b c d e m1 m2 guard : Bool) :
    (guard && Bool.xor
      (Bool.xor (Bool.xor (Bool.xor (((a && b) && c) && d && e)
        (m2 && ((a && b) && c))) (m2 && ((a && b) && c)))
        (m1 && (a && b))) (m1 && (a && b))) =
    (guard && a && b && c && d && e) := by bv_decide

theorem shared_guard (g h p : Bool) :
    Bool.xor (g && p) (h && p) = (Bool.xor g h && p) := by bv_decide

-- Resource counts of the recorded local edits, excluding classical
-- instructions from the paid quantum-gate count.
def paid (xs : List Nat) : Nat :=
  (xs.filter (fun x => x == 48 || x == 49 || x == 50)).length
theorem local_resources :
    ([129,16,1,17,49,129,16,1] : List Nat).length = 8 ∧
    ([17,49,144,144] : List Nat).length = 4 ∧
    paid [129,16,1,17,49,129,16,1] = paid [17,49,144,144] ∧
    ([160,49,129,16,16,16,1,33] : List Nat).length = 8 ∧
    ([49,33,144,144,160] : List Nat).length = 5 ∧
    paid [160,49,129,16,16,16,1,33] = paid [49,33,144,144,160] := by decide

end GVQCC.V8
