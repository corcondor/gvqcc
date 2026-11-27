import Mathlib

namespace GVQCC.FixedProjective
open Polynomial

/-- The regular branch divides the larger degree bound by a quadratic. -/
theorem regular_bound {F : Type*} [Field F]
    (A B h g Q : Polynomial F) (a b : ℕ)
    (ha : A.natDegree ≤ a) (hb : B.natDegree ≤ b)
    (hab : b+1 ≤ a) (hh : h.natDegree ≤ 1)
    (hg : g.natDegree = 2) (hg0 : g ≠ 0)
    (hQ : Q ≠ 0) (he : A+h*B = g*Q) :
    Q.natDegree+2 ≤ a := by
  have hprod : (h*B).natDegree ≤ a := by
    calc
      _ ≤ h.natDegree+B.natDegree := natDegree_mul_le
      _ ≤ a := by omega
  have hsum : (A+h*B).natDegree ≤ a :=
    le_trans (natDegree_add_le A (h*B)) (max_le ha hprod)
  rw [he, natDegree_mul hg0 hQ, hg] at hsum
  omega

/-- Division of a vanishing smaller component has the same two-degree drop. -/
theorem singular_bound {F : Type*} [Field F]
    (B g Q : Polynomial F) (b : ℕ) (hb : B.natDegree ≤ b)
    (hg : g.natDegree=2) (hg0 : g ≠ 0) (hq : Q ≠ 0)
    (he : B=g*Q) : Q.natDegree+2 ≤ b := by
  rw [he, natDegree_mul hg0 hq, hg] at hb
  omega

/-- Signed bounds, with physical orientation swapped after every slot. -/
def step (a b : ℤ) (d : Bool) : ℤ × ℤ :=
  if d then (b,a-2) else (b-2,a)

theorem step_sum (a b : ℤ) (d : Bool) :
    (step a b d).1+(step a b d).2=a+b-2 := by
  cases d <;> simp [step] <;> omega

theorem step_odd_gap (a b k : ℤ) (d : Bool) (h : a-b=2*k+1) :
    ∃ l : ℤ, (step a b d).1-(step a b d).2=2*l+1 := by
  cases d
  · refine ⟨-k-2, ?_⟩
    simp [step]
    omega
  · refine ⟨-k, ?_⟩
    simp [step]
    omega

def bounds : List Bool → ℤ × ℤ
  | [] => (34,35)
  | d::ds => let p := bounds ds; step p.1 p.2 d

theorem bounds_sum (ds : List Bool) :
    (bounds ds).1+(bounds ds).2=69-2*(ds.length : ℤ) := by
  induction ds with
  | nil => decide
  | cons d ds ih =>
    change (step (bounds ds).1 (bounds ds).2 d).1 +
      (step (bounds ds).1 (bounds ds).2 d).2 = _
    rw [step_sum, ih, List.length_cons]
    omega

theorem final_negative (ds : List Bool) (h : ds.length=35) :
    (bounds ds).1<0 ∨ (bounds ds).2<0 := by
  have hs := bounds_sum ds
  rw [h] at hs
  omega

/-- At a pole the legal quotient in the opposite direction is zero. -/
theorem singular_quotient {F : Type*} [Field F] (x y : F) (hx : x=0) :
    x/y=0 := by simp [hx]

/-- Bézout witness survives the regular division; no common factor is introduced. -/
theorem regular_coprime_witness {R : Type*} [CommRing R]
    (A B h g Q p q : R) (he : A+h*B=g*Q)
    (hw : p*A+q*B=1) : (p*g)*Q+(q-p*h)*B=1 := by
  calc
    _ = p*(g*Q)+(q-p*h)*B := by ring
    _ = p*A+q*B := by rw [← he]; ring
    _ = 1 := hw

theorem singular_coprime_witness {R : Type*} [CommRing R]
    (A B g Q p q : R) (he : B=g*Q) (hw : p*A+q*B=1) :
    p*A+(q*g)*Q=1 := by
  calc
    _ = p*A+q*(g*Q) := by ring
    _ = 1 := by rw [← he, hw]

/-- Multiplication on a first-order Hermite jet. -/
def scale {R : Type*} [CommRing R] (g : R) (p : R × R) : R × R :=
  (g*p.1,g*p.2+p.1)

theorem scale_twice {R : Type*} [CommRing R] (g u v : R)
    (h : (2 : R)=0) :
    scale g (scale g (u,v))=(g^2*u,g^2*v) := by
  apply Prod.ext
  · simp [scale]
    ring
  · change g*(g*v+u)+g*u=g^2*v
    calc
      _ = g^2*v+2*g*u := by ring
      _ = _ := by rw [h, zero_mul, zero_mul, add_zero]

theorem scale_inverse {F : Type*} [Field F] (g u v : F)
    (hg : g ≠ 0) (h : (2 : F)=0) :
    scale g (u/g,(v+u/g)/g)=(u,v) := by
  have hu : g*(u/g)=u := by field_simp
  have hv : g*((v+u/g)/g)=v+u/g := by field_simp
  apply Prod.ext
  · exact hu
  · change g*((v+u/g)/g)+u/g=v
    rw [hv]
    calc
      _ = v+2*(u/g) := by ring
      _ = _ := by rw [h, zero_mul, add_zero]

/-- HMR scratch is recoverable from the output in either control branch. -/
theorem controlled_scale_debt {F : Type*} [Field F] (g x : F)
    (hg : g ≠ 0) :
    (g+1)*x=(g⁻¹+1)*(g*x) := by
  have hi : g⁻¹*g=1 := inv_mul_cancel₀ hg
  calc
    _ = g*x+x := by ring
    _ = (g⁻¹*g)*x+g*x := by rw [hi, one_mul]; ring
    _ = _ := by ring

theorem packed_budget : 35*24+9+51=900 := by decide

theorem zero_word_metadata {A : Type*} (a b z : A) (t : Bool)
    (h : t=true → b=z) :
    (if t then (b,a) else (a,b)).1 =
      (if t then z else a) := by
  cases t
  · rfl
  · simp [h rfl]

end GVQCC.FixedProjective

#print axioms GVQCC.FixedProjective.regular_bound
#print axioms GVQCC.FixedProjective.singular_bound
#print axioms GVQCC.FixedProjective.step_sum
#print axioms GVQCC.FixedProjective.step_odd_gap
#print axioms GVQCC.FixedProjective.bounds_sum
#print axioms GVQCC.FixedProjective.final_negative
#print axioms GVQCC.FixedProjective.singular_quotient
#print axioms GVQCC.FixedProjective.regular_coprime_witness
#print axioms GVQCC.FixedProjective.singular_coprime_witness
#print axioms GVQCC.FixedProjective.scale_twice
#print axioms GVQCC.FixedProjective.scale_inverse
#print axioms GVQCC.FixedProjective.controlled_scale_debt
#print axioms GVQCC.FixedProjective.packed_budget
#print axioms GVQCC.FixedProjective.zero_word_metadata
