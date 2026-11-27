import Std

namespace GVQCC.SharedOverlap

def bx (x y : Bool) := Bool.xor x y

theorem same_factor (a b c t : Bool) :
    bx (bx t (a && b)) (a && c) = bx t (a && bx b c) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem same_factor_dirty_controls (a b c t : Bool) :
    (a, bx (bx b c) c, c, bx t (a && bx b c)) =
      (a, b, c, bx (bx t (a && b)) (a && c)) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem same_product_fanout (a b x y : Bool) :
    (bx x (a && b), bx (bx x y) (bx x (a && b))) =
      (bx x (a && b), bx y (a && b)) := by
  cases a <;> cases b <;> cases x <;> cases y <;> decide

theorem same_product_cancel (a b t : Bool) :
    bx (bx t (a && b)) (a && b) = t := by
  cases a <;> cases b <;> cases t <;> decide

theorem phase_factor (a b x y : Bool) :
    bx (a && b && x) (a && b && y) = (a && b && bx x y) := by
  cases a <;> cases b <;> cases x <;> cases y <;> decide

theorem mixed_phase (a b x z : Bool) :
    bx (x && z) (bx x (a && b) && z) = (a && b && z) := by
  cases a <;> cases b <;> cases x <;> cases z <;> decide

/-- The same physical product is valid at both uses if the independently
tracked operand expressions prove equality. HMR outcome is arbitrary. -/
theorem retained_phase (a b c d m : Bool) (h : (a && b) = (c && d)) :
    bx (m && a && b) (m && c && d) = false := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases m <;> simp_all [bx, Bool.xor]

def fan (p : Bool) (xs : List Bool) := xs.map (fun x => bx x p)

theorem multi_target_retention (a b c d m : Bool) (xs : List Bool)
    (h : (a && b) = (c && d)) :
    (fan (a && b) xs, bx (m && a && b) (m && c && d)) =
      (fan (c && d) xs, false) := by
  rw [retained_phase a b c d m h, h]

/-- Moving a fixed update across an arbitrary intervening transformation
requires exactly this commutation hypothesis; no global legality is inferred. -/
theorem transport_pair {S : Type} (f : S → S) (u v : S → S)
    (h : ∀ x, f (u x) = u (f x)) (s : S) :
    v (f (u s)) = v (u (f s)) := by rw [h]

theorem costs_pair (n : Nat) : n+1 < n+2 := by omega
theorem costs_shared (n : Nat) (h : 2 ≤ n) : 1 < n := by omega

#print axioms same_factor
#print axioms same_factor_dirty_controls
#print axioms same_product_fanout
#print axioms same_product_cancel
#print axioms phase_factor
#print axioms mixed_phase
#print axioms retained_phase
#print axioms multi_target_retention
#print axioms transport_pair
#print axioms costs_pair
#print axioms costs_shared

/-- An offset survives a target-only XOR update, independently of the
guard and the original wire's value. Reads, reset, measurement and swaps
are excluded by the physical interval certificate. -/
theorem offset_write (x p z guard : Bool) :
    bx (bx x p) (guard && z) = bx (bx x (guard && z)) p := by
  cases x <;> cases p <;> cases z <;> cases guard <;> decide

def applyWrites (x : Bool) (xs : List Bool) :=
  xs.foldl bx x

theorem offset_many_writes (x p : Bool) (xs : List Bool) :
    applyWrites (bx x p) xs = bx (applyWrites x xs) p := by
  induction xs generalizing x with
  | nil => rfl
  | cons a rest ih =>
    change applyWrites (bx (bx x p) a) rest =
      bx (applyWrites (bx x a) rest) p
    have h : bx (bx x p) a = bx (bx x a) p := by
      cases x <;> cases p <;> cases a <;> decide
    rw [h, ih]

theorem offset_zero_end (x p : Bool) (xs : List Bool)
    (h : applyWrites x xs = false) :
    applyWrites (bx x p) xs = p := by
  rw [offset_many_writes, h]
  cases p <;> decide

#print axioms offset_write
#print axioms offset_many_writes
#print axioms offset_zero_end

end GVQCC.SharedOverlap
