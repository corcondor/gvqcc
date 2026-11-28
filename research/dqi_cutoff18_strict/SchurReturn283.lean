import Mathlib

namespace GVQCC.SchurReturn283
open scoped BigOperators

section Scalar
variable {F : Type*} [Field F]

/-- Scalar Schur chart with a retained nonmonic leading factor. -/
def scalarLift (d p t : F) : F := (p-t)/d

theorem scalar_lift_eq (d p t : F) (hd : d ≠ 0) :
    d*scalarLift d p t+t=p := by
  unfold scalarLift
  field_simp
  ring

theorem scalar_lift_unique (d p t x : F) (hd : d ≠ 0)
    (h : d*x+t=p) : x=scalarLift d p t := by
  unfold scalarLift
  apply (eq_div_iff hd).2
  rw [mul_comm x d]
  exact eq_sub_of_add_eq h

theorem scalar_schur_rhs (d p t c a : F) (hd : d ≠ 0) :
    c*scalarLift d p t+a = (a-c*t/d)+c*p/d := by
  unfold scalarLift
  field_simp
  ring

/-- Both original equations are equivalent to the reduced system.
    In particular the first equation is restored, not discarded. -/
theorem scalar_schur_iff (d p t c a r x : F) (hd : d ≠ 0) :
    (d*x+t=p ∧ c*x+a=r) ↔
      (x=scalarLift d p t ∧ a-c*t/d=r-c*p/d) := by
  constructor
  · rintro ⟨h1,h2⟩
    have hx := scalar_lift_unique d p t x hd h1
    refine ⟨hx,?_⟩
    rw [hx,scalar_schur_rhs d p t c a hd] at h2
    exact eq_sub_of_add_eq h2
  · rintro ⟨rfl,h2⟩
    constructor
    · exact scalar_lift_eq d p t hd
    · rw [scalar_schur_rhs d p t c a hd,h2,sub_add_cancel]

/-- Move a shared reciprocal through a complete dot product. -/
theorem dot_shared_reciprocal {I : Type*} [Fintype I] (a b : I → F)
    (d : F) :
    (∑ i, (a i/d)*b i) = (∑ i, a i*b i)/d := by
  simp only [div_eq_mul_inv, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem scalar_schur_dot {I : Type*} [Fintype I] (a row y : I → F)
    (c d : F) :
    (∑ i, (a i-c*row i/d)*y i) =
      (∑ i, a i*y i)-c*(∑ i,row i*y i)/d := by
  simp only [sub_mul, Finset.sum_sub_distrib, div_eq_mul_inv, Finset.mul_sum,
    Finset.sum_mul]
  congr 1
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- Actual Schur reduction on arbitrary remaining rows and RHS. -/
theorem scalar_system_equiv {I : Type*} [Fintype I]
    (A : I → I → F) (row col y rhs : I → F) (d p x : F)
    (hd : d≠0) :
    (d*x+(∑ j, row j*y j)=p ∧
      ∀ i, col i*x+(∑ j,A i j*y j)=rhs i) ↔
    (x=scalarLift d p (∑ j,row j*y j) ∧
      ∀ i, (∑ j,(A i j-col i*row j/d)*y j)=rhs i-col i*p/d) := by
  constructor
  · rintro ⟨h1,h2⟩
    refine ⟨scalar_lift_unique _ _ _ _ hd h1,?_⟩
    intro i
    rw [scalar_schur_dot]
    exact ((scalar_schur_iff d p (∑ j,row j*y j) (col i)
      (∑ j,A i j*y j) (rhs i) x hd).mp ⟨h1,h2 i⟩).2
  · rintro ⟨hx,h2⟩
    refine ⟨?_,?_⟩
    · rw [hx]
      exact scalar_lift_eq _ _ _ hd
    · intro i
      have hrow := h2 i
      rw [scalar_schur_dot] at hrow
      exact ((scalar_schur_iff d p (∑ j,row j*y j) (col i)
        (∑ j,A i j*y j) (rhs i) x hd).mpr ⟨hx,hrow⟩).2

/-- Invertibility of the original system implies a nonzero entry.
    If no diagonal pivot exists, an off-diagonal pivot must exist. -/
theorem zero_diagonal_has_offdiag {I : Type*} [Fintype I] [Nonempty I]
    (A : I → I → F) (hd : ∀ i,A i i=0)
    (hker : ∀ x : I → F, (∀ i, (∑ j,A i j*x j)=0) → x=0) :
    ∃ i j, i≠j ∧ A i j≠0 := by
  classical
  by_contra! h
  have hz (i j : I) : A i j=0 := by
    by_cases he : i=j
    · subst j
      exact hd i
    · exact h i j he
  have he := hker (fun _ => (1:F)) (by intro i; simp [hz])
  obtain ⟨i⟩ := ‹Nonempty I›
  exact one_ne_zero (congrFun he i)

end Scalar

section TwoPivot
variable {F : Type*} [Field F]

/-- Alternating 2-by-2 block [0 b; b 0]. No inverse of a zero diagonal
    is formed, and one reciprocal is shared by both outputs. -/
def pairLift (b p q : F) : F × F := (q/b,p/b)

theorem pair_lift_eq (b p q : F) (hb : b≠0) :
    (b*(pairLift b p q).2,b*(pairLift b p q).1)=(p,q) := by
  apply Prod.ext <;> simp only [pairLift] <;> field_simp

theorem pair_lift_unique (b p q x y : F) (hb : b≠0)
    (h1 : b*y=p) (h2 : b*x=q) : (x,y)=pairLift b p q := by
  apply Prod.ext
  · change x=q/b
    exact (eq_div_iff hb).2 (by rw [mul_comm x b,h2])
  · change y=p/b
    exact (eq_div_iff hb).2 (by rw [mul_comm y b,h1])

theorem pair_schur_rhs (b p q t u c d a : F) (hb : b≠0) :
    c*((q-u)/b)+d*((p-t)/b)+a =
      a-(c*u+d*t)/b+(c*q+d*p)/b := by
  field_simp
  ring

theorem pair_schur_iff (b p q t u c d a r x y : F) (hb : b≠0) :
    (b*y+t=p ∧ b*x+u=q ∧ c*x+d*y+a=r) ↔
      ((x,y)=pairLift b (p-t) (q-u) ∧
        a-(c*u+d*t)/b=r-(c*q+d*p)/b) := by
  constructor
  · rintro ⟨h1,h2,h3⟩
    have hxy := pair_lift_unique b (p-t) (q-u) x y hb
      (eq_sub_of_add_eq h1) (eq_sub_of_add_eq h2)
    refine ⟨hxy,?_⟩
    have hx := congrArg Prod.fst hxy
    have hy := congrArg Prod.snd hxy
    change x=(q-u)/b at hx
    change y=(p-t)/b at hy
    rw [hx,hy,pair_schur_rhs b p q t u c d a hb] at h3
    exact eq_sub_of_add_eq h3
  · rintro ⟨hxy,h3⟩
    have hx := congrArg Prod.fst hxy
    have hy := congrArg Prod.snd hxy
    change x=(q-u)/b at hx
    change y=(p-t)/b at hy
    refine ⟨?_,?_,?_⟩
    · rw [hy]
      field_simp
      ring
    · rw [hx]
      field_simp
      ring
    · rw [hx,hy,pair_schur_rhs b p q t u c d a hb,h3,sub_add_cancel]

/-- Schur complement after the off-diagonal pivot preserves symmetry. -/
def pairUpdate {I : Type*} (A : I → I → F) (u v : I → F) (b : F)
    (i j : I) : F := A i j-(u i*v j+v i*u j)/b

theorem pair_update_symmetric {I : Type*} (A : I → I → F) (u v : I → F)
    (b : F) (hs : ∀ i j,A i j=A j i) (i j : I) :
    pairUpdate A u v b i j=pairUpdate A u v b j i := by
  unfold pairUpdate
  rw [hs i j]
  congr 1
  ring

theorem pair_update_diagonal {I : Type*} (A : I → I → F) (u v : I → F)
    (b : F) (h2 : (2:F)=0) (i : I) :
    pairUpdate A u v b i i=A i i := by
  unfold pairUpdate
  have h : u i*v i+v i*u i=0 := by
    calc
      _ = (2:F)*(u i*v i) := by ring
      _ = 0 := by rw [h2,zero_mul]
  rw [h,zero_div,sub_zero]

theorem pair_update_dot {I : Type*} [Fintype I] (A : I → I → F)
    (u v y : I → F) (b : F) (i : I) :
    (∑ j,pairUpdate A u v b i j*y j) =
    (∑ j,A i j*y j)-
      (u i*(∑ j,v j*y j)+v i*(∑ j,u j*y j))/b := by
  simp only [pairUpdate, sub_mul, Finset.sum_sub_distrib, div_eq_mul_inv,
    Finset.mul_sum, Finset.sum_mul, add_mul, Finset.sum_add_distrib]
  congr 1
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro j _
  ring

/-- Two-pivot branch equivalent to the original equations for every RHS,
    including singular diagonal charts. -/
theorem pair_system_equiv {I : Type*} [Fintype I]
    (A : I → I → F) (u v z rhs : I → F) (b p q x y : F) (hb : b≠0) :
    (b*y+(∑ j,u j*z j)=p ∧ b*x+(∑ j,v j*z j)=q ∧
      ∀ i, u i*x+v i*y+(∑ j,A i j*z j)=rhs i) ↔
    ((x,y)=pairLift b (p-∑ j,u j*z j) (q-∑ j,v j*z j) ∧
      ∀ i, (∑ j,pairUpdate A u v b i j*z j)=rhs i-(u i*q+v i*p)/b) := by
  constructor
  · rintro ⟨h1,h2,h3⟩
    refine ⟨pair_lift_unique _ _ _ _ _ hb (eq_sub_of_add_eq h1)
      (eq_sub_of_add_eq h2),?_⟩
    intro i
    rw [pair_update_dot]
    exact ((pair_schur_iff b p q (∑ j,u j*z j) (∑ j,v j*z j)
      (u i) (v i) (∑ j,A i j*z j) (rhs i) x y hb).mp ⟨h1,h2,h3 i⟩).2
  · rintro ⟨hxy,h3⟩
    have hx := congrArg Prod.fst hxy
    have hy := congrArg Prod.snd hxy
    change x=(q-∑ j,v j*z j)/b at hx
    change y=(p-∑ j,u j*z j)/b at hy
    refine ⟨?_,?_,?_⟩
    · rw [hy]
      field_simp
      ring
    · rw [hx]
      field_simp
      ring
    · intro i
      have hrow := h3 i
      rw [pair_update_dot] at hrow
      exact ((pair_schur_iff b p q (∑ j,u j*z j) (∑ j,v j*z j)
        (u i) (v i) (∑ j,A i j*z j) (rhs i) x y hb).mpr ⟨hxy,hrow⟩).2

end TwoPivot

#print axioms scalar_lift_eq
#print axioms scalar_lift_unique
#print axioms scalar_schur_rhs
#print axioms scalar_schur_iff
#print axioms dot_shared_reciprocal
#print axioms scalar_schur_dot
#print axioms scalar_system_equiv
#print axioms zero_diagonal_has_offdiag
#print axioms pair_lift_eq
#print axioms pair_lift_unique
#print axioms pair_schur_rhs
#print axioms pair_schur_iff
#print axioms pair_update_symmetric
#print axioms pair_update_diagonal
#print axioms pair_update_dot
#print axioms pair_system_equiv
end GVQCC.SchurReturn283
