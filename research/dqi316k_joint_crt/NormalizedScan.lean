namespace NormalizedScan

-- All arguments lie in the nonzero multiplicative group of the field.
theorem normalized_inverse {F : Type} (mul : F → F → F) (inv : F → F)
    (assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (comm : ∀ a b, mul a b = mul b a)
    (inv_mul : ∀ a b, inv (mul a b) = mul (inv a) (inv b))
    (inv_inv : ∀ a, inv (inv a) = a)
    (x d b : F) :
    inv (mul x (mul d (inv b))) = mul b (inv (mul x d)) := by
  rw [← assoc x d (inv b), inv_mul, inv_inv, comm (inv (mul x d)) b]

theorem padded_root {F : Type} (mul : F → F → F) (zero : F)
    (mul_eq_zero : ∀ a b, mul a b = zero ↔ a = zero ∨ b = zero)
    (p d : F) (hp : p ≠ zero) :
    mul p d = zero ↔ d = zero := by
  rw [mul_eq_zero]
  constructor
  · intro h
    cases h with
    | inl h => exact False.elim (hp h)
    | inr h => exact h
  · intro h
    exact Or.inr h

theorem scan_guard {F : Type} (zero a b : F) (root : Bool)
    (h : a = b) :
    (if root then a else zero) = (if root then b else zero) := by
  rw [h]

#print axioms normalized_inverse
#print axioms padded_root
#print axioms scan_guard
end NormalizedScan
