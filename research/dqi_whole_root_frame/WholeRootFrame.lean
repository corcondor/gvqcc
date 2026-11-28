import Std

namespace GVQCC.WholeRootFrame

def flip (x f : Bool) : Bool := Bool.xor x f

/-- Frame transport of the actual target update, including dirty targets. -/
theorem ccx_transport (x y t fx fy ft : Bool) :
    Bool.xor (flip t ft) (flip x fx && flip y fy) =
      flip (Bool.xor t (flip x fx && flip y fy)) ft := by
  cases x <;> cases y <;> cases t <;> cases fx <;> cases fy <;> cases ft <;> decide

theorem frame_restore (x f : Bool) : flip (flip x f) f = x := by
  cases x <;> cases f <;> decide

theorem phase_ccz_transport (p x y z fx fy fz : Bool) :
    Bool.xor p (flip x fx && flip y fy && flip z fz) =
      Bool.xor (flip x fx && flip y fy && flip z fz) p := by
  cases p <;> cases x <;> cases y <;> cases z <;>
    cases fx <;> cases fy <;> cases fz <;> decide

/-- Repayment with negative literals while keeping their X frame live. -/
theorem repay_transport (p m x y fx fy : Bool) :
    Bool.xor p (m && (flip x fx && flip y fy)) =
      Bool.xor p ((m && flip x fx) && flip y fy) := by
  cases p <;> cases m <;> cases x <;> cases y <;>
    cases fx <;> cases fy <;> decide

theorem exact_debt (p m x y fx fy : Bool) :
    Bool.xor (Bool.xor p (m && (flip x fx && flip y fy)))
      ((m && flip x fx) && flip y fy) = p := by
  cases p <;> cases m <;> cases x <;> cases y <;>
    cases fx <;> cases fy <;> decide

theorem hmr_unflipped_target (t m p : Bool) :
    (false, Bool.xor p (m && flip t false)) =
      (false, Bool.xor p (m && t)) := by
  cases t <;> cases m <;> cases p <;> decide

theorem guarded_toggle_pool (t g h p : Bool) :
    Bool.xor (Bool.xor t (g && p)) (h && p) =
      Bool.xor t (Bool.xor g h && p) := by
  cases t <;> cases g <;> cases h <;> cases p <;> decide

theorem same_guard_cancel (t g p : Bool) :
    Bool.xor (Bool.xor t (g && p)) (g && p) = t := by
  cases t <;> cases g <;> cases p <;> decide

def swapIndex (u v i : Nat) : Nat :=
  if i = u then v else if i = v then u else i

theorem swapIndex_involutive (u v i : Nat) :
    swapIndex u v (swapIndex u v i) = i := by
  by_cases h : u = v
  · subst v
    by_cases hi : i = u <;> simp_all [swapIndex]
  · have h' : v ≠ u := fun e => h e.symm
    by_cases hi : i = u
    · subst i
      simp_all [swapIndex]
    · by_cases hj : i = v
      · subst i
        simp_all [swapIndex]
      · simp_all [swapIndex]

/-- Under a logical-to-physical layout l, swapping logical positions is
represented by composing l with the same transposition. -/
theorem swap_relabel (p : Nat → Bool) (l : Nat → Nat) (u v i : Nat) :
    (fun j => p (l (swapIndex u v j))) i =
      (fun j => p (l j)) (swapIndex u v i) := rfl

theorem swap_relabel_restore (p : Nat → Bool) (l : Nat → Nat) (u v i : Nat) :
    p (l (swapIndex u v (swapIndex u v i))) = p (l i) := by
  rw [swapIndex_involutive]

theorem measured_root_frame_count : (77 - 55 : Nat) * 4024 = 88528 := by decide
theorem permutation_count : (287496 - 105132 : Nat) = 182364 := by decide
theorem full_count : (87704819 - 182364 - 88528 : Nat) = 87433927 := by decide
theorem paid_count : (311202 + 6686 + 108 : Nat) = 317996 := by decide

#print axioms ccx_transport
#print axioms frame_restore
#print axioms phase_ccz_transport
#print axioms repay_transport
#print axioms exact_debt
#print axioms hmr_unflipped_target
#print axioms guarded_toggle_pool
#print axioms same_guard_cancel
#print axioms swapIndex_involutive
#print axioms swap_relabel
#print axioms swap_relabel_restore
#print axioms measured_root_frame_count
#print axioms permutation_count
#print axioms full_count
#print axioms paid_count
end GVQCC.WholeRootFrame
