import Init

namespace GVQCC.SharedFrame316
def x := Bool.xor
def add {I : Type} (a b : I → Bool) : I → Bool :=
  fun i => x (a i) (b i)
def scale {I : Type} (s : Bool) (a : I → Bool) : I → Bool :=
  fun i => s && a i

/-- A rank-one update in any invertible linear output frame has the
same effect on arbitrary dirty outputs; there is no clean-target hypothesis. -/
theorem output_transport {I : Type} (F G : (I → Bool) → (I → Bool))
    (inv : ∀ a, G (F a) = a)
    (lin : ∀ a b, F (add a b) = add (F a) (F b))
    (sc : ∀ s a, F (scale s a) = scale s (F a))
    (y d : I → Bool) (p : Bool) :
    G (add (F y) (scale p (F d))) = add y (scale p d) := by
  rw [← sc, ← lin, inv]

/-- Independent products may be scheduled in any order in the common
output space, since their controls do not read the output. -/
theorem commute_updates {I : Type} (y a b : I → Bool) (p q : Bool) :
    add (add y (scale p a)) (scale q b) =
      add (add y (scale q b)) (scale p a) := by
  funext i
  simp only [add, scale, x]
  cases (y i) <;> cases (a i) <;> cases (b i) <;>
    cases p <;> cases q <;> decide

theorem cnot_involution (a b : Bool) : x a (x a b) = b := by
  cases a <;> cases b <;> decide

theorem complement_product (a b : Bool) :
    (!a) && b = x b (a && b) := by
  cases a <;> cases b <;> decide

theorem distribute_product (a b c : Bool) :
    a && x b c = x (a && b) (a && c) := by
  cases a <;> cases b <;> cases c <;> decide

/-- Exact active/inactive scope merge used by the abstract interpreter. -/
theorem scope_merge (oldVal newVal k : Bool) :
    x oldVal (k && x oldVal newVal) =
      (if k then newVal else oldVal) := by
  cases oldVal <;> cases newVal <;> cases k <;> decide

/-- A reset is safe only if the actual target is the witnessed product.
For every outcome the HMR phase is repaid exactly. -/
theorem exact_hmr_witness (p m a b t : Bool) (h : t = (a && b)) :
    x (x p (m && t)) (m && (a && b)) = p := by
  subst t
  cases p <;> cases m <;> cases a <;> cases b <;> decide

theorem hmr_witness_necessary (a b t : Bool)
    (h : ∀ m : Bool, x (m && t) (m && (a && b)) = false) :
    t = (a && b) := by
  have ht := h true
  cases a <;> cases b <;> cases t <;> simp_all [x]

#print axioms output_transport
#print axioms commute_updates
#print axioms cnot_involution
#print axioms complement_product
#print axioms distribute_product
#print axioms scope_merge
#print axioms exact_hmr_witness
#print axioms hmr_witness_necessary
end GVQCC.SharedFrame316
