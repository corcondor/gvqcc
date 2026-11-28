import Std

namespace MultiMeasurementDebt

def bx (a b : Bool) : Bool := Bool.xor a b
def perturb (p d x : Bool) : Bool := bx x (p && d)

theorem xor_four (a b c d : Bool) :
    bx (bx a b) (bx c d) = bx (bx a c) (bx b d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem and_distrib (p a b : Bool) :
    (p && bx a b) = bx (p && a) (p && b) := by
  cases p <;> cases a <;> cases b <;> decide

def selectThird (g h c d : Bool) : Bool :=
  if g then bx c (h && d) else d

def forwardPair (g h c d : Bool) : Bool × Bool :=
  let s := if !g && h then (d,c) else (c,d)
  (bx s.1 (g && h && s.2), s.2)

def reversePair (g h c d : Bool) : Bool × Bool :=
  let t := bx c (g && h && d)
  if !g && h then (d,t) else (t,d)

theorem guarded_cubic_joint (g h a b c d : Bool) :
    bx (g && a && b && c) (h && a && b && d) =
      ((g || h) && a && b && selectThird g h c d) := by
  cases g <;> cases h <;> cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem forward_selected (g h c d : Bool) :
    ((g || h) && (forwardPair g h c d).1) =
    ((g || h) && selectThird g h c d) := by
  cases g <;> cases h <;> cases c <;> cases d <;> decide

theorem pair_restored (g h c d : Bool) :
    reversePair g h (forwardPair g h c d).1 (forwardPair g h c d).2 = (c,d) := by
  cases g <;> cases h <;> cases c <;> cases d <;> decide

theorem same_plane (g h a b c : Bool) :
    bx (g && a && b && c) (h && a && b && c) =
    (bx g h && a && b && c) := by
  cases g <;> cases h <;> cases a <;> cases b <;> cases c <;> decide

theorem actual_cost (g h : Bool) :
    (if g then 1 else 0 : Nat) + (if h then 1 else 0) =
    (if g || h then 1 else 0) + (if g && h then 1 else 0) := by
  cases g <;> cases h <;> decide

theorem hmr_delta (p d m x : Bool) :
    bx (m && perturb p d x) (m && x) = (p && d && m) := by
  cases p <;> cases d <;> cases m <;> cases x <;> decide

theorem cx_delta (p d e x y : Bool) :
    bx (perturb p d x) (perturb p e y) = perturb p (bx d e) (bx x y) := by
  cases p <;> cases d <;> cases e <;> cases x <;> cases y <;> decide

theorem phase_bridge (m a b c t : Bool) :
    bx (m && c && bx t (a && b)) (m && c && t) = (m && c && a && b) := by
  cases m <;> cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem perturb_twice (p d x : Bool) :
    perturb p d (perturb p d x) = x := by
  cases p <;> cases d <;> cases x <;> decide

theorem recover_omitted (x y r : Bool) (h : x = bx y r) : y = bx x r := by
  subst x
  cases y <;> cases r <;> decide

def phaseFold (xs : List Bool) : Bool := xs.foldr bx false

-- Every local difference is p times a known coefficient; their sum is
-- p times the XOR of all coefficients. No independence assumption on m.
theorem fold_debt (xs : List (Bool × Bool × Bool)) (p : Bool)
    (h : ∀ s ∈ xs, bx s.1 s.2.1 = (p && s.2.2)) :
    bx (phaseFold (xs.map Prod.fst))
       (phaseFold (xs.map (fun s => s.2.1))) =
       (p && phaseFold (xs.map (fun s => s.2.2))) := by
  induction xs with
  | nil => cases p <;> decide
  | cons x xs ih =>
    have hx := h x (by simp)
    have ht := ih (fun s hs => h s (by simp [hs]))
    change bx (bx x.1 (phaseFold (xs.map Prod.fst)))
      (bx x.2.1 (phaseFold (xs.map (fun s => s.2.1)))) =
      (p && bx x.2.2 (phaseFold (xs.map (fun s => s.2.2))))
    rw [xor_four, hx, ht, ← and_distrib]

theorem repayment_cancel (p r : Bool) :
    bx (p && r) (p && r) = false := by
  cases p <;> cases r <;> decide

-- Full-space counterexample: the unqualified projected update is not
-- reversible. A reachable-state invariant is necessary to use it.
def badProjection (x : Bool × Bool) : Bool × Bool :=
  (x.1, bx x.2 (x.1 && x.2))

theorem bad_projection_collision :
    badProjection (true,false) = badProjection (true,true) := by decide

theorem bad_projection_not_injective :
    ¬ Function.Injective badProjection := by
  intro h
  have he := h bad_projection_collision
  exact (by decide : (true,false) ≠ (true,true)) he

theorem shear_invariant_inverse (p : Bool → Bool) (d x : Bool)
    (h : p (perturb (p x) d x) = p x) :
    perturb (p (perturb (p x) d x)) d (perturb (p x) d x) = x := by
  rw [h]
  exact perturb_twice (p x) d x

#print axioms xor_four
#print axioms and_distrib
#print axioms guarded_cubic_joint
#print axioms forward_selected
#print axioms pair_restored
#print axioms same_plane
#print axioms actual_cost
#print axioms hmr_delta
#print axioms cx_delta
#print axioms phase_bridge
#print axioms perturb_twice
#print axioms recover_omitted
#print axioms fold_debt
#print axioms repayment_cancel
#print axioms bad_projection_collision
#print axioms bad_projection_not_injective
#print axioms shear_invariant_inverse

end MultiMeasurementDebt
