import Mathlib

theorem v80_product_difference {R : Type*} [CommRing R]
    (a b da db : R) :
    (a + da) * (b + db) - a * b = a * db + b * da + da * db := by ring

theorem v80_discrete_product {R : Type*} [CommRing R]
    (u v du dv : R) :
    (u + du) * (v + dv) - u * v = du * (v + dv) + u * dv := by ring

theorem v80_half_bezout {R : Type*} [CommRing R]
    (x e o a b : R) (h2 : (2 : R) = 0) (h : a * e + b * o = 1) :
    (x * a^2 + b^2) * o^2 + a^2 * (e^2 + x * o^2) = 1 := by
  calc
    _ = (a * e + b * o)^2 + (2 : R) * (x * a^2 * o^2 - a * e * b * o) := by ring
    _ = 1 := by rw [h, h2]; simp
