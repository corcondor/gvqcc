import Mathlib

namespace GVQCC.V81

local instance : Fact (Nat.Prime 2) := ⟨by decide⟩

theorem tower_embedding_iff (d : ℕ) (hd : d ≠ 0) :
    Nonempty (GaloisField 2 d →ₐ[ZMod 2] GaloisField 2 12) ↔ d ∣ 12 := by
  rw [FiniteField.nonempty_algHom_iff_finrank_dvd,
    GaloisField.finrank 2 hd,
    GaloisField.finrank 2 (by decide : (12 : ℕ) ≠ 0)]

theorem field_card : Nat.card (GaloisField 2 12) = 4096 := by
  rw [GaloisField.card 2 (by decide : (12 : ℕ) ≠ 0)] <;> decide

theorem trace_pairing {F : Type*} [Field F] [Finite F]
    [Algebra (ZMod (ringChar F)) F] {a : F} (ha : a ≠ 0) :
    ∃ b : F, Algebra.trace (ZMod (ringChar F)) F (a * b) ≠ 0 :=
  FiniteField.trace_to_zmod_nondegenerate F ha

theorem square_add {R : Type*} [CommRing R] (h2 : (2 : R) = 0) (x y : R) :
    (x + y)^2 = x^2 + y^2 := by
  calc
    (x + y)^2 = x^2 + y^2 + (2 : R) * x * y := by ring
    _ = x^2 + y^2 := by rw [h2]; ring

theorem additive_next {R : Type*} [CommRing R] (h2 : (2 : R) = 0)
    (t : R → R) (ha : ∀ x y, t (x + y) = t x + t y) (c x y : R) :
    (t (x + y))^2 + c * t (x + y) =
      (t x)^2 + c * t x + ((t y)^2 + c * t y) := by
  rw [ha, square_add h2]
  ring

theorem normalized_step {R : Type*} [CommRing R] (t : R → R)
    (ha : ∀ x y, t (x + y) = t x + t y) (b : R) (hb : t b = 1) (x : R) :
    t (x + b) = t x + 1 := by rw [ha, hb]

theorem reversible_butterfly {R : Type*} [CommRing R] (h2 : (2 : R) = 0)
    (a p c : R) : ((a + c*p) + p) + (c+1)*p = a := by
  calc
    ((a + c*p) + p) + (c+1)*p = a + (2 : R)*(c+1)*p := by ring
    _ = a := by rw [h2]; ring

theorem half_bezout {R : Type*} [CommRing R]
    (x e o a b : R) (h2 : (2 : R) = 0) (h : a * e + b * o = 1) :
    (x * a^2 + b^2) * o^2 + a^2 * (e^2 + x * o^2) = 1 := by
  calc
    _ = (a * e + b * o)^2 + (2 : R) * (x * a^2 * o^2 - a * e * b * o) := by ring
    _ = 1 := by rw [h, h2]; simp

end GVQCC.V81

#print axioms GVQCC.V81.tower_embedding_iff
#print axioms GVQCC.V81.reversible_butterfly
#print axioms GVQCC.V81.half_bezout
