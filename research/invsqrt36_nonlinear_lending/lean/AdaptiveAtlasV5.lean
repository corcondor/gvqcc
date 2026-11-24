import Init

/-! V5: measured reconstruction and chart transition.
The actual candidate is conditional on a reachable-state identity checked
separately by the all-domain BDD comparator. No whole-oracle proof is claimed. -/
namespace GVQCCV5

def bx := Bool.xor

theorem measured_reconstruction (a b t l m phase : Bool)
    (h : bx t (a && b) = l) :
    (l, bx (bx (bx phase (m && t)) (m && (a && b))) (m && l)) =
    (bx t (a && b), phase) := by
  cases a <;> cases b <;> cases t <;> cases l <;> cases m <;> cases phase <;> simp_all [bx]

-- Actual V4 emitted instruction 47113: CCX 24 28 25.
-- The affine decoder is q13 XOR q18 XOR q19 XOR q28 XOR q29 XOR q34.
def actualL (q13 q18 q19 q28 q29 q34 : Bool) : Bool :=
  bx (bx (bx (bx (bx q13 q18) q19) q28) q29) q34

theorem actual47113 (q13 q18 q19 q24 q25 q28 q29 q34 m phase : Bool)
    (h : bx q25 (q24 && q28) = actualL q13 q18 q19 q28 q29 q34) :
    (actualL q13 q18 q19 q28 q29 q34,
      bx (bx (bx phase (m && q25)) (m && (q24 && q28)))
        (m && actualL q13 q18 q19 q28 q29 q34)) =
    (bx q25 (q24 && q28), phase) :=
  measured_reconstruction q24 q28 q25 (actualL q13 q18 q19 q28 q29 q34) m phase h

theorem affine_phase_expansion (m a b : Bool) :
    (m && bx a b) = bx (m && a) (m && b) := by
  cases m <;> cases a <;> cases b <;> decide

theorem chart_exchange (d e correction : Bool)
    (h : bx d e = correction) : bx e correction = d := by
  cases d <;> cases e <;> cases correction <;> simp_all [bx]

theorem chart_exchange_inverse (d e correction : Bool)
    (h : bx d e = correction) : bx d correction = e := by
  cases d <;> cases e <;> cases correction <;> simp_all [bx]

end GVQCCV5
