import Init
import Std

namespace GVQCC.DirectHermite316

section FieldIdentities

variable {F : Type}
variable (zero one : F) (add mul : F → F → F) (inv : F → F)

def sq (mul : F → F → F) (a : F) : F := mul a a

/-- Frobenius is additive, derived from characteristic two and distributivity. -/
theorem square_add (a b : F)
    (ha : ∀ x y z, add (add x y) z = add x (add y z))
    (hc : ∀ x y, add x y = add y x)
    (hz : ∀ x, add x zero = x) (h2 : ∀ x, add x x = zero)
    (hm : ∀ x y, mul x y = mul y x)
    (ld : ∀ x y z, mul x (add y z) = add (mul x y) (mul x z))
    (rd : ∀ x y z, mul (add x y) z = add (mul x z) (mul y z)) :
    sq mul (add a b) = add (sq mul a) (sq mul b) := by
  unfold sq
  rw [ld, rd, rd, hm b a]
  calc
    _ = add (mul a a) (add (mul a b) (add (mul a b) (mul b b))) := ha _ _ _
    _ = add (mul a a) (add (add (mul a b) (mul a b)) (mul b b)) := by rw [ha]
    _ = add (mul a a) (mul b b) := by rw [h2, hc zero, hz]

theorem square_mul (a b : F)
    (ha : ∀ x y z, mul (mul x y) z = mul x (mul y z))
    (hc : ∀ x y, mul x y = mul y x) :
    sq mul (mul a b) = mul (sq mul a) (sq mul b) := by
  unfold sq
  calc
    mul (mul a b) (mul a b) = mul a (mul b (mul a b)) := ha _ _ _
    _ = mul a (mul (mul b a) b) := by rw [ha]
    _ = mul a (mul (mul a b) b) := by rw [hc b a]
    _ = mul a (mul a (mul b b)) := by rw [ha]
    _ = mul (mul a a) (mul b b) := (ha _ _ _).symm

/-- No root-free-padding coprimality assumption is used for this leaf test. -/
theorem half_root (a b rho x : F)
    (hAdd : ∀ u v, sq mul (add u v) = add (sq mul u) (sq mul v))
    (hMul : ∀ u v, sq mul (mul u v) = mul (sq mul u) (sq mul v))
    (hRho : sq mul rho = x)
    (hZero : ∀ u, sq mul u = zero ↔ u = zero) :
    add (sq mul a) (mul x (sq mul b)) = zero ↔
      add a (mul rho b) = zero := by
  rw [← hRho, ← hMul, ← hAdd]
  exact hZero _

theorem half_numerator (p q rho x : F)
    (hAdd : ∀ u v, sq mul (add u v) = add (sq mul u) (sq mul v))
    (hMul : ∀ u v, sq mul (mul u v) = mul (sq mul u) (sq mul v))
    (hRho : sq mul rho = x) :
    sq mul (add p (mul rho q)) =
      add (sq mul p) (mul x (sq mul q)) := by
  rw [hAdd, hMul, hRho]

/-- The leaf uses only the square-rooted denominator and numerator. -/
theorem half_ratio (p d e u : F)
    (hMul : ∀ x y, sq mul (mul x y) = mul (sq mul x) (sq mul y))
    (hInv : sq mul (inv d) = inv (sq mul d))
    (hA : ∀ x y z, mul (mul x y) z = mul x (mul y z))
    (hOne : ∀ x, mul x one = x)
    (hd : mul (sq mul d) (inv (sq mul d)) = one)
    (h : sq mul p = mul (mul u e) (sq mul d)) :
    sq mul (mul p (inv d)) = mul u e := by
  rw [hMul, hInv, h, hA, hd, hOne]

theorem weighted_cancel (p d e u : F)
    (h : p = mul (mul u e) d)
    (hA : ∀ x y z, mul (mul x y) z = mul x (mul y z))
    (hC : ∀ x y, mul x y = mul y x)
    (hOne : ∀ x, mul x one = x)
    (hd : mul d (inv d) = one)
    (hu : mul u (inv u) = one) :
    mul (mul p (inv d)) (inv u) = e := by
  rw [h, hA (mul u e), hd, hOne, hC u e, hA, hu, hOne]

/-- At a simple physical root d(a)=0, a common factor can be retained.
    The derivative product law is explicit rather than an assumption of
    coprime numerator and denominator. -/
theorem common_factor_root (g d dp gp : F)
    (hd : d = zero)
    (hM0 : ∀ x, mul x zero = zero)
    (hZ : ∀ x, add zero x = x) :
    add (mul gp d) (mul g dp) = mul g dp := by rw [hd, hM0, hZ]

theorem common_factor_ratio (g n dp e : F)
    (h : n = mul e dp)
    (hA : ∀ x y z, mul (mul x y) z = mul x (mul y z))
    (hC : ∀ x y, mul x y = mul y x) :
    mul g n = mul e (mul g dp) := by
  rw [h, ← hA, hC g e, hA]

/-- A zero-fiber Hermite head must not erase the derivative coordinate. -/
theorem zero_fiber_injective {A : Type} (zero : A)
    (f : A → A → A × A) (h : ∀ v, f zero v = (zero,v))
    (u v : A) (he : f zero u = f zero v) : u = v := by
  rw [h, h] at he
  exact congrArg Prod.snd he

end FieldIdentities

section Phase
def parity (xs : List Bool) : Bool := xs.foldr Bool.xor false

theorem xor_assoc (a b c : Bool) :
    Bool.xor (Bool.xor a b) c = Bool.xor a (Bool.xor b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem parity_append (a b : List Bool) :
    parity (a ++ b) = Bool.xor (parity a) (parity b) := by
  induction a with
  | nil => change parity b = Bool.xor false (parity b); cases parity b <;> decide
  | cons x xs ih =>
    change Bool.xor x (parity (xs ++ b)) = Bool.xor (Bool.xor x (parity xs)) (parity b)
    rw [ih, xor_assoc]

theorem parity_zip_xor (xs ys : List Bool) (h : xs.length = ys.length) :
    parity (List.zipWith Bool.xor xs ys) = Bool.xor (parity xs) (parity ys) := by
  induction xs generalizing ys with
  | nil =>
    cases ys with
    | nil => rfl
    | cons y ys => simp at h
  | cons x xs ih =>
    cases ys with
    | nil => simp at h
    | cons y ys =>
      have hh : xs.length = ys.length := by simpa using h
      have hr := ih ys hh
      change Bool.xor (Bool.xor x y) (parity (List.zipWith Bool.xor xs ys)) =
        Bool.xor (Bool.xor x (parity xs)) (Bool.xor y (parity ys))
      rw [hr]
      cases x <;> cases y <;> cases parity xs <;> cases parity ys <;> decide

theorem residual_cancel (pre total : Bool) :
    Bool.xor pre (Bool.xor total pre) = total := by
  cases pre <;> cases total <;> decide

theorem root7 (a b c d e f g h i j k l : Bool) :
    (((a && b && c) && (d && e && f)) &&
      ((g && h && i) && (j && k && l))) =
    (a && b && c && d && e && f && g && h && i && j && k && l) := by
  simp only [Bool.and_assoc]

theorem hmr_product_repay (a b m : Bool) :
    Bool.xor ((a && b) && m) ((a && b) && m) = false := by
  cases a <;> cases b <;> cases m <;> decide

theorem phase_linear_pullback (a b m : Bool) :
    ((Bool.xor a b) && m) = Bool.xor (a && m) (b && m) := by
  cases a <;> cases b <;> cases m <;> decide

theorem physical_full_composition {S C M : Type} (forward : S → C)
    (back : C → S) (phase : S → M → Bool) (p : S → M → Bool)
    (leaf : C → M → Bool) (residual : M → M)
    (hback : ∀ s, back (forward s) = s)
    (hphase : ∀ s m, leaf (forward s) (residual m) = Bool.xor (phase s m) (p s m))
    (s : S) (m : M) :
    (back (forward s), m, Bool.xor (p s m) (leaf (forward s) (residual m))) =
      (s,m,phase s m) := by
  rw [hback, hphase, residual_cancel]

end Phase
#print axioms square_add
#print axioms square_mul
#print axioms half_root
#print axioms half_numerator
#print axioms half_ratio
#print axioms weighted_cancel
#print axioms common_factor_root
#print axioms common_factor_ratio
#print axioms zero_fiber_injective
#print axioms xor_assoc
#print axioms parity_append
#print axioms parity_zip_xor
#print axioms residual_cancel
#print axioms root7
#print axioms hmr_product_repay
#print axioms phase_linear_pullback
#print axioms physical_full_composition
end GVQCC.DirectHermite316

