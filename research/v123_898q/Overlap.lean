import Std

namespace GVQCC.V123
def bx (a b : Bool) : Bool := Bool.xor a b

-- Normalize the unordered pair (a,b) within {a,b,a⊕b}, without losing
-- the linear correction. This is the symbolic tracker's product key.
theorem normalize_left (a b : Bool) :
    bx (b && bx a b) b = (a && b) := by
  cases a <;> cases b <;> decide
theorem normalize_right (a b : Bool) :
    bx (a && bx a b) a = (a && b) := by
  cases a <;> cases b <;> decide
theorem complement_left (a b : Bool) :
    (!a && b) = bx (a && b) b := by
  cases a <;> cases b <;> decide
theorem complement_right (a b : Bool) :
    (a && !b) = bx (a && b) a := by
  cases a <;> cases b <;> decide
theorem complement_both (a b : Bool) :
    (!a && !b) = bx true (bx a (bx b (a && b))) := by
  cases a <;> cases b <;> decide
theorem equal_product (a b : Bool) :
    (a && a) = a ∧ (a && !a) = false ∧ (a && b) = (b && a) := by
  cases a <;> cases b <;> decide

def fan (p : Bool) (xs : List Bool) := xs.map (fun x => bx x p)

-- Reuse a single computed product across any number of target registers.
-- Product equality is a required physical interval obligation.
theorem shared_product (a b c d m : Bool) (xs : List Bool)
    (h : (a && b) = (c && d)) :
    (fan (a && b) xs,
      bx (m && a && b) (m && c && d)) = (fan (c && d) xs, false) := by
  have z : bx (m && a && b) (m && c && d) = false := by
    cases a <;> cases b <;> cases c <;> cases d <;> cases m <;> simp_all [bx, Bool.xor]
  rw [z,h]

-- If the target is not read until the last use, duplicate CCX cancel.
theorem duplicate_cancel (x a b : Bool) :
    bx (bx x (a && b)) (a && b) = x := by
  cases x <;> cases a <;> cases b <;> decide

-- Transport each guarded write across the target's X-basis measurement.
theorem guarded_sink (x a b m g : Bool) :
    (m && bx x (g && a && b)) =
      bx (m && x) (g && m && a && b) := by
  cases x <;> cases a <;> cases b <;> cases m <;> cases g <;> decide

theorem guarded_linear_sink (x a m g : Bool) :
    (m && bx x (g && a)) = bx (m && x) (g && m && a) := by
  cases x <;> cases a <;> cases m <;> cases g <;> decide

def applyWrites (x : Bool) (ws : List Bool) : Bool := ws.foldl bx x
theorem phase_writes (x m : Bool) (ws : List Bool) :
    (m && applyWrites x ws) = applyWrites (m && x) (ws.map (fun z => m && z)) := by
  induction ws generalizing x with
  | nil => rfl
  | cons a as ih =>
    change (m && applyWrites (bx x a) as) =
      applyWrites (bx (m && x) (m && a)) (as.map (fun z => m && z))
    rw [ih]
    have h : (m && bx x a) = bx (m && x) (m && a) := by
      cases m <;> cases x <;> cases a <;> decide
    rw [h]

-- Correct a shared product in the phase itself using a live representation.
theorem phase_product_linear (a b p t g : Bool) (h : (a && b) = p) :
    (g && a && b && t) = (g && p && t) := by
  cases a <;> cases b <;> cases p <;> cases t <;> cases g <;> simp_all

theorem cost_fanout (n : Nat) (hn : 1 < n) : 1 < n := hn

#print axioms normalize_left
#print axioms normalize_right
#print axioms complement_left
#print axioms complement_right
#print axioms complement_both
#print axioms equal_product
#print axioms shared_product
#print axioms duplicate_cancel
#print axioms guarded_sink
#print axioms guarded_linear_sink
#print axioms phase_writes
#print axioms phase_product_linear
#print axioms cost_fanout
-- More general sharing: p and a*b need not be equal, only differ by
-- an affine function of the current two controls. No extra paid correction.
def correction (a b l r c : Bool) := bx (l && a) (bx (r && b) c)

theorem affine_target (a b l r c t : Bool) :
    bx (bx t (bx (a && b) (correction a b l r c)))
       (correction a b l r c) = bx t (a && b) := by
  cases a <;> cases b <;> cases l <;> cases r <;> cases c <;> cases t <;> decide

theorem affine_phase (a b l r c m : Bool) :
    bx (m && bx (a && b) (correction a b l r c))
       (bx (m && a && b)
          (bx (m && l && a) (bx (m && r && b) (m && c)))) = false := by
  cases a <;> cases b <;> cases l <;> cases r <;> cases c <;> cases m <;> decide

theorem affine_shared (a b l r c p t m : Bool)
    (h : p = bx (a && b) (correction a b l r c)) :
    (bx (bx t p) (correction a b l r c),
     bx (m && p) (bx (m && a && b)
          (bx (m && l && a) (bx (m && r && b) (m && c))))) =
    (bx t (a && b), false) := by
  rw [h, affine_target, affine_phase]

#print axioms affine_target
#print axioms affine_phase
#print axioms affine_shared

end GVQCC.V123
