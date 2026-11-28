import Mathlib.RingTheory.AdjoinRoot
import Mathlib.Tactic.Ring

open Polynomial
namespace GVQCC.JetRing
noncomputable section
variable {K : Type*} [CommRing K]

def g (k : K) : Polynomial K := X^2 + X + C k
abbrev A (k : K) := AdjoinRoot (g k ^ 2)
abbrev B (k : K) := AdjoinRoot (g k)
def ep (k : K) : Polynomial (B k) := X^2
abbrev D (k : K) := AdjoinRoot (ep k)

def ia (k : K) : K →+* A k := AdjoinRoot.of (g k ^ 2)
def ib (k : K) : K →+* B k := AdjoinRoot.of (g k)
def idu (k : K) : B k →+* D k := AdjoinRoot.of (ep k)
def id0 (k : K) : K →+* D k := (idu k).comp (ib k)
def x (k : K) : A k := AdjoinRoot.root (g k ^ 2)
def y (k : K) : B k := AdjoinRoot.root (g k)
def e (k : K) : D k := AdjoinRoot.root (ep k)
def yd (k : K) : D k := idu k (y k)
def delta (k : K) : A k := x k ^ 2 + x k + ia k k

theorem two_map {R S : Type*} [CommRing R] [CommRing S]
    (h : (2 : R) = 0) (f : R →+* S) : (2 : S) = 0 := by
  calc
    (2 : S) = 1 + 1 := (one_add_one_eq_two).symm
    _ = f ((1 : R) + 1) := by simp only [map_add, map_one]
    _ = 0 := by rw [one_add_one_eq_two, h, map_zero]

theorem twice {R : Type*} [CommRing R] (h : (2 : R) = 0) (a : R) :
    a + a = 0 := by
  calc
    a + a = 2 * a := by ring
    _ = 0 := by rw [h, zero_mul]

theorem shift {R : Type*} [CommRing R] (h : (2 : R) = 0) (a b c : R) :
    (a+b)^2+(a+b)+c = (a^2+a+c)+(b^2+b) := by
  calc
    (a+b)^2+(a+b)+c = (a^2+a+c)+(b^2+b)+2*a*b := by ring
    _ = _ := by rw [h]; ring

theorem delta_nil (k : K) : delta k ^ 2 = 0 := by
  have hr := AdjoinRoot.eval₂_root (g k ^ 2)
  change (g k ^ 2).eval₂ (ia k) (x k) = 0 at hr
  simpa only [delta, g, eval₂_add, eval₂_pow, eval₂_X, eval₂_C] using hr

theorem y_root (k : K) : y k ^ 2 + y k + ib k k = 0 := by
  have hr := AdjoinRoot.eval₂_root (g k)
  change (g k).eval₂ (ib k) (y k) = 0 at hr
  simpa only [g, eval₂_add, eval₂_pow, eval₂_X, eval₂_C] using hr

theorem e_nil (k : K) : e k ^ 2 = 0 := by
  have hr := AdjoinRoot.eval₂_root (ep k)
  change (ep k).eval₂ (idu k) (e k) = 0 at hr
  simpa only [ep, eval₂_pow, eval₂_X] using hr

theorem yd_root (k : K) : yd k ^ 2 + yd k + id0 k k = 0 := by
  simpa only [yd, id0, RingHom.comp_apply, map_add, map_pow, map_zero]
    using congrArg (fun t : B k => idu k t) (y_root k)

def forward (k : K) (h : (2 : K) = 0) : A k →+* D k :=
  AdjoinRoot.lift (id0 k) (yd k + e k) (by
    simp only [g, eval₂_pow, eval₂_add, eval₂_X, eval₂_C]
    rw [shift (two_map h (id0 k))]
    simp only [yd_root, e_nil, zero_add])

def baseToA (k : K) (h : (2 : K) = 0) : B k →+* A k :=
  AdjoinRoot.lift (ia k) (x k + delta k) (by
    simp only [g, eval₂_pow, eval₂_add, eval₂_X, eval₂_C]
    rw [shift (two_map h (ia k))]
    change delta k + (delta k ^ 2 + delta k) = 0
    rw [delta_nil, zero_add, twice (two_map h (ia k))])

def backward (k : K) (h : (2 : K) = 0) : D k →+* A k :=
  AdjoinRoot.lift (baseToA k h) (delta k) (by
    simpa only [ep, eval₂_pow, eval₂_X] using delta_nil k)

theorem forward_x (k : K) (h : (2 : K) = 0) :
    forward k h (x k) = yd k + e k := by
  simp only [forward, x, AdjoinRoot.lift_root]

theorem forward_ia (k : K) (h : (2 : K) = 0) (r : K) :
    forward k h (ia k r) = id0 k r := by
  simp only [forward, ia, AdjoinRoot.lift_of]

theorem backward_e (k : K) (h : (2 : K) = 0) :
    backward k h (e k) = delta k := by
  simp only [backward, e, AdjoinRoot.lift_root]

theorem backward_yd (k : K) (h : (2 : K) = 0) :
    backward k h (yd k) = x k + delta k := by
  simp only [backward, yd, idu, AdjoinRoot.lift_of, baseToA, y, AdjoinRoot.lift_root]

theorem backward_id0 (k : K) (h : (2 : K) = 0) (r : K) :
    backward k h (id0 k r) = ia k r := by
  simp only [backward, id0, RingHom.comp_apply, idu, AdjoinRoot.lift_of, baseToA, ib]

theorem forward_delta (k : K) (h : (2 : K) = 0) :
    forward k h (delta k) = e k := by
  unfold delta
  rw [map_add, map_add, map_pow, forward_x, forward_ia, shift (two_map h (id0 k))]
  simp only [yd_root, e_nil, zero_add]

theorem left_hom (k : K) (h : (2 : K) = 0) :
    (backward k h).comp (forward k h) = RingHom.id (A k) := by
  apply AdjoinRoot.ringHom_ext
  · apply RingHom.ext
    intro r
    change backward k h (forward k h (ia k r)) = ia k r
    rw [forward_ia, backward_id0]
  · change backward k h (forward k h (x k)) = x k
    rw [forward_x, map_add, backward_yd, backward_e, add_assoc,
      twice (two_map h (ia k)), add_zero]

theorem right_hom (k : K) (h : (2 : K) = 0) :
    (forward k h).comp (backward k h) = RingHom.id (D k) := by
  apply AdjoinRoot.ringHom_ext
  · apply AdjoinRoot.ringHom_ext
    · apply RingHom.ext
      intro r
      change forward k h (backward k h (id0 k r)) = id0 k r
      rw [backward_id0, forward_ia]
    · change forward k h (backward k h (yd k)) = yd k
      rw [backward_yd, map_add, forward_x, forward_delta, add_assoc,
        twice (two_map h (id0 k)), add_zero]
  · change forward k h (backward k h (e k)) = e k
    rw [backward_e, forward_delta]

/-- Actual ring equivalence K[X]/(g²) ≃ (K[Y]/g)[ε]/(ε²).
No irreducibility assumption is needed for the equivalence. -/
def jetEquiv (k : K) (h : (2 : K) = 0) : A k ≃+* D k where
  toFun := forward k h
  invFun := backward k h
  left_inv a := DFunLike.congr_fun (left_hom k h) a
  right_inv a := DFunLike.congr_fun (right_hom k h) a
  map_mul' := map_mul (forward k h)
  map_add' := map_add (forward k h)

#print axioms delta_nil
#print axioms yd_root
#print axioms forward_delta
#print axioms left_hom
#print axioms right_hom
#print axioms jetEquiv
end
end GVQCC.JetRing
