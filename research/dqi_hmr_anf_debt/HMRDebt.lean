import Std

namespace GVQCC.HMRDebt

def xor (a b : Bool) : Bool := Bool.xor a b
def phase (g m v : Bool) : Bool := g && m && v

theorem xor_assoc (a b c : Bool) :
    xor (xor a b) c = xor a (xor b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem cancel_pair (a b : Bool) : xor a (xor b b) = a := by
  cases a <;> cases b <;> decide

theorem squarefree (a b : Bool) : (a && a && b) = (a && b) := by
  cases a <;> cases b <;> decide

theorem distribute (a b c : Bool) :
    (a && xor b c) = xor (a && b) (a && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem guard_snapshot (g m h v : Bool) :
    phase g m (h && v) = phase (g && h) m v := by
  cases g <;> cases m <;> cases h <;> cases v <;> decide

theorem guarded_reset (g x : Bool) :
    xor x (g && xor x false) = (x && !g) := by
  cases g <;> cases x <;> decide

theorem conditional_update (g old new : Bool) :
    xor old (g && xor old new) = (if g then new else old) := by
  cases g <;> cases old <;> cases new <;> decide

theorem phase_equiv_iff (before old new : Bool) :
    xor before old = xor before new ↔ xor old new = false := by
  cases before <;> cases old <;> cases new <;> decide

theorem measured_target_not_enough (g m x old : Bool) :
    xor (phase g m x) old = false ↔ old = phase g m x := by
  cases g <;> cases m <;> cases x <;> cases old <;> decide

theorem transport_exact (p g m x old new : Bool) (h : old = new) :
    xor (xor p (phase g m x)) old = xor (xor p (phase g m x)) new := by
  rw [h]

theorem independent_opaque_atom (a b c : Bool) :
    xor (a && xor b c) (xor (a && b) (a && c)) = false := by
  cases a <;> cases b <;> cases c <;> decide

theorem pairwise_pool (p a b c d : Bool)
    (h₁ : xor a b = false) (h₂ : xor c d = false) :
    xor (xor p a) c = xor (xor p b) d := by
  cases p <;> cases a <;> cases b <;> cases c <;> cases d <;>
    simp_all [xor, Bool.xor]

end GVQCC.HMRDebt

#print axioms GVQCC.HMRDebt.xor_assoc
#print axioms GVQCC.HMRDebt.cancel_pair
#print axioms GVQCC.HMRDebt.squarefree
#print axioms GVQCC.HMRDebt.distribute
#print axioms GVQCC.HMRDebt.guard_snapshot
#print axioms GVQCC.HMRDebt.guarded_reset
#print axioms GVQCC.HMRDebt.conditional_update
#print axioms GVQCC.HMRDebt.phase_equiv_iff
#print axioms GVQCC.HMRDebt.measured_target_not_enough
#print axioms GVQCC.HMRDebt.transport_exact
#print axioms GVQCC.HMRDebt.independent_opaque_atom
#print axioms GVQCC.HMRDebt.pairwise_pool


namespace GVQCC.HMRGraph

def shear (q : Nat → Bool) (u v : Nat) : Nat → Bool :=
  fun i => if i = v then Bool.xor (q v) (q u) else q i

theorem shear_twice (q : Nat → Bool) (u v : Nat) (h : u ≠ v) :
    shear (shear q u v) u v = q := by
  funext i
  by_cases hi : i = v
  · subst i
    simp only [shear, ite_eq_right h]
    cases q v <;> cases q u <;> decide
  · simp only [shear, ite_eq_right hi]

theorem graph_edge_transport (u v w : Bool) :
    (Bool.xor v u && w) = Bool.xor (v && w) (u && w) := by
  cases u <;> cases v <;> cases w <;> decide

theorem adjacent_edge_transport (u v : Bool) :
    (u && Bool.xor v u) = Bool.xor (u && v) u := by
  cases u <;> cases v <;> decide

theorem phase_conjugation (P : (Nat → Bool) → Bool) (q : Nat → Bool)
    (u v : Nat) (h : u ≠ v) :
    P (shear (shear q u v) u v) = P q := by
  rw [shear_twice q u v h]

theorem guarded_phase_conjugation (P : (Nat → Bool) → Bool)
    (q : Nat → Bool) (g : Bool) (u v : Nat) (h : u ≠ v) :
    (if g then P (shear (shear q u v) u v) else false) =
      (if g then P q else false) := by
  rw [shear_twice q u v h]

end GVQCC.HMRGraph

#print axioms GVQCC.HMRGraph.shear_twice
#print axioms GVQCC.HMRGraph.graph_edge_transport
#print axioms GVQCC.HMRGraph.adjacent_edge_transport
#print axioms GVQCC.HMRGraph.phase_conjugation
#print axioms GVQCC.HMRGraph.guarded_phase_conjugation
