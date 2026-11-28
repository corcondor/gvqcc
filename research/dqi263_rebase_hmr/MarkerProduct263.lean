import Init
import Std
namespace GVQCC.MarkerProduct263

def product {F : Type} (one : F) (mul : F → F → F) : List F → F
  | [] => one
  | x :: xs => mul x (product one mul xs)

theorem product_zero_iff {F : Type} (zero one : F) (mul : F → F → F)
    (h1 : one ≠ zero)
    (h0 : ∀ a b, mul a b = zero ↔ a = zero ∨ b = zero)
    (xs : List F) :
    product one mul xs = zero ↔ zero ∈ xs := by
  induction xs with
  | nil => simp [product, h1]
  | cons a xs ih => simp [product, h0, ih, eq_comm]

/-- A marker factor is present precisely when its public constant is listed,
    assuming the other polynomial factors have nonzero evaluations there. -/
theorem marker_membership {F K : Type} (zero one : F) (mul : F → F → F)
    (h1 : one ≠ zero)
    (h0 : ∀ a b, mul a b = zero ↔ a = zero ∨ b = zero)
    (k : K) (ev : K → F) (he : ∀ x, ev x = zero ↔ x = k)
    (ks : List K) (physical : List F) (hp : zero ∉ physical) :
    product one mul (ks.map ev ++ physical) = zero ↔ k ∈ ks := by
  rw [product_zero_iff zero one mul h1 h0]
  simp [hp, he]

theorem marker_swap {K : Type} (k k' : K) (old new : List K)
    (ho : k ∈ old) (hn : k' ∈ new)
    (_hc : k' ∉ old) (_hd : k ∉ new) :
    (k ∈ old ↔ k' ∈ new) ∧ (k' ∈ old ↔ k ∈ new) := by
  constructor
  · exact ⟨fun _ => hn, fun _ => ho⟩
  · exact ⟨fun h => False.elim (_hc h), fun h => False.elim (_hd h)⟩

theorem factor_nonzero_from_embedding {F L : Type} (zero : L)
    (embed : F → L) (sub : L → L → L)
    (zeroiff : ∀ a b, sub a b = zero ↔ a = b)
    (r : L) (hn : ∀ a, r ≠ embed a) (a : F) :
    sub r (embed a) ≠ zero := by
  intro h
  exact hn a ((zeroiff _ _).mp h)

/-- A marker's two tests may be replaced by an HMR phase repayment only
    when the semantic membership predicate is preserved by the map. -/
theorem marker_hmr {S : Type} (f : S → S) (old new : S → Bool)
    (h : ∀ s, old s = new (f s)) (s : S) (m : Bool) :
    Bool.xor (m && old s) (if m then new (f s) else false) = false := by
  rw [h s]
  cases m <;> cases new (f s) <;> decide

#print axioms product_zero_iff
#print axioms marker_membership
#print axioms marker_swap
#print axioms factor_nonzero_from_embedding
#print axioms marker_hmr
end GVQCC.MarkerProduct263
