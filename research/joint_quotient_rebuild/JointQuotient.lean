import Lean

namespace GVQCC.JointQuotient

def add {A : Type} (x y : A → Bool) : A → Bool := fun i => Bool.xor (x i) (y i)
def mul {A : Type} (x y : A → Bool) : A → Bool := fun i => x i && y i

theorem add_exchange {A : Type} (a b r : A → Bool) :
    add (add a b) r = add (add a r) b := by
  funext i
  unfold add
  cases ha : a i <;> cases hb : b i <;> cases hr : r i <;> decide

theorem same_class_sum {A : Type} (a b r : A → Bool) :
    add (add a r) (add b r) = add a b := by
  funext i
  unfold add
  cases ha : a i <;> cases hb : b i <;> cases hr : r i <;> decide

theorem split_reconstruct {A : Type} (u a b : A → Bool)
    (ha : ∀ i, u i = false → a i = false)
    (hb : ∀ i, u i = true → b i = false) :
    mul u (add a b) = a := by
  funext i
  unfold mul add
  cases h : u i
  · simp [ha i h]
  · simp [hb i h]

/-- C and U are additive spaces, with C contained in U. A quotient
class has a product representative u*v, v in C, iff the class has
representatives supported on both complementary masks of u. -/
theorem product_class_iff {A : Type}
    (C U : (A → Bool) → Prop)
    (hC : ∀ x y, C x → C y → C (add x y))
    (hU : ∀ x y, U x → U y → U (add x y))
    (hCU : ∀ x, C x → U x)
    (u r : A → Bool) :
    (∃ v, C v ∧ U (mul u v) ∧ C (add (mul u v) r)) ↔
    (∃ a b, U a ∧ U b ∧ C (add a r) ∧ C (add b r) ∧
      (∀ i, u i = false → a i = false) ∧
      (∀ i, u i = true → b i = false)) := by
  constructor
  · intro h
    rcases h with ⟨v, hv, hp, hc⟩
    refine ⟨mul u v, add (mul u v) v, hp, hU _ _ hp (hCU _ hv), hc, ?_, ?_, ?_⟩
    · rw [add_exchange]
      exact hC _ _ hc hv
    · intro i hi
      simp [mul, hi]
    · intro i hi
      simp [add, mul, hi]
  · intro h
    rcases h with ⟨a, b, hua, hub, hca, hcb, ha, hb⟩
    have hc := hC _ _ hca hcb
    rw [same_class_sum] at hc
    have hx := split_reconstruct u a b ha hb
    exact ⟨add a b, hc, hx.symm ▸ hua, hx.symm ▸ hca⟩

/-- Exact finite difference of a product; the mixed term matters. -/
theorem product_difference (a b da db : Bool) :
    Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
    Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

/-- Zero and all one-hot measurement histories do not certify adaptive phase. -/
theorem onehot_insufficient :
    (false && false = false) ∧ (true && false = false) ∧
    (false && true = false) ∧ (true && true = true) := by decide

/-- A phase-only change leaves the restoration error unchanged. -/
theorem phase_only_preserves_value_error (actual expected phase correction : Bool) :
    (actual, Bool.xor phase correction).1 ≠ expected ↔ actual ≠ expected := by rfl

end GVQCC.JointQuotient
#print axioms GVQCC.JointQuotient.add_exchange
#print axioms GVQCC.JointQuotient.same_class_sum
#print axioms GVQCC.JointQuotient.split_reconstruct
#print axioms GVQCC.JointQuotient.product_class_iff
#print axioms GVQCC.JointQuotient.product_difference
#print axioms GVQCC.JointQuotient.onehot_insufficient
#print axioms GVQCC.JointQuotient.phase_only_preserves_value_error
