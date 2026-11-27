import Init
namespace GVQCC.EarlyHMR

def commit (m : Bool) : Bool × Bool := (Bool.xor false m, false)

theorem delayed_commit (m : Bool) : commit m = (m, false) := by
  cases m <;> decide

theorem phase_transport (p q m extra : Bool) :
    Bool.xor (Bool.xor p extra) (m && q) =
      Bool.xor (Bool.xor p (m && q)) extra := by
  cases p <;> cases q <;> cases m <;> cases extra <;> decide

/-- f may inspect and modify the original classical destination and all other
state, but not the measured wire or fresh private classical slot. The Boolean
third component returned by f is its phase contribution. Coupling outcome m
proves exact final values and phase, including arbitrary destination reuse. -/
def original {A : Type} (f : A → Bool → A × Bool × Bool)
    (x : A) (q b p m : Bool) : A × Bool × Bool × Bool × Bool :=
  let (x', _, extra) := f x b
  (x', false, m, false, Bool.xor (Bool.xor p extra) (m && q))

def moved {A : Type} (f : A → Bool → A × Bool × Bool)
    (x : A) (q b p m : Bool) : A × Bool × Bool × Bool × Bool :=
  let p' := Bool.xor p (m && q)
  let tmp := m
  let (x', _, extra) := f x b
  let (b', tmp') := commit tmp
  (x', false, b', tmp', Bool.xor p' extra)

theorem delayed_hmr_equivalence {A : Type}
    (f : A → Bool → A × Bool × Bool) (x : A) (q b p m : Bool) :
    original f x q b p m = moved f x q b p m := by
  cases hf : f x b with
  | mk x' v =>
    cases v with
    | mk b' extra =>
      simp only [original, moved, hf, delayed_commit]
      rw [phase_transport]

theorem original_destination_preserved (b m : Bool) :
    (b, m).1 = b := by rfl

theorem zero_wire_after_hmr (q m : Bool) :
    (false, m, m && q).1 = false := by rfl

theorem move_from_zero (v : Bool) :
    (Bool.xor false v, Bool.xor v (Bool.xor false v)) = (v, false) := by
  cases v <;> decide

theorem phase_relabel (m q p : Bool) :
    Bool.xor p (m && (Bool.xor false q)) = Bool.xor p (m && q) := by
  cases m <;> cases q <;> cases p <;> decide

theorem two_independent_masks (p a b m n : Bool) :
    Bool.xor (Bool.xor p (m && a)) (n && b) =
      Bool.xor (Bool.xor p (n && b)) (m && a) := by
  cases p <;> cases a <;> cases b <;> cases m <;> cases n <;> decide

end GVQCC.EarlyHMR
#print axioms GVQCC.EarlyHMR.delayed_commit
#print axioms GVQCC.EarlyHMR.phase_transport
#print axioms GVQCC.EarlyHMR.delayed_hmr_equivalence
#print axioms GVQCC.EarlyHMR.original_destination_preserved
#print axioms GVQCC.EarlyHMR.zero_wire_after_hmr
#print axioms GVQCC.EarlyHMR.move_from_zero
#print axioms GVQCC.EarlyHMR.phase_relabel
#print axioms GVQCC.EarlyHMR.two_independent_masks
