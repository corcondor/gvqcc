import Mathlib
namespace GVQCC.TensorRank
open scoped BigOperators
theorem transpose_character {I J : Type*} [Fintype I] [Fintype J]
    (A : J → I → ZMod 2) (m : J → ZMod 2) (h : I → ZMod 2) :
    (∑ j, m j * (∑ i, A j i * h i)) = ∑ i, (∑ j, m j * A j i) * h i := by
  classical
  calc
    _ = ∑ j, ∑ i, (m j * A j i) * h i := by
      simp_rw [Finset.mul_sum, mul_assoc]
    _ = ∑ i, ∑ j, (m j * A j i) * h i := Finset.sum_comm
    _ = _ := by simp only [Finset.sum_mul]
theorem product_order (x a b c d : ZMod 2) :
    (x+a*b)+c*d = (x+c*d)+a*b := by ring
theorem pivot_product (x a b f : ZMod 2) :
    (x+f)+a*b+f = x+a*b := by
  have hf : f+f=0 := by
    calc f+f = 2*f := by ring
         _ = 0 := by have h : (2:ZMod 2)=0 := by decide
                     rw [h,zero_mul]
  calc (x+f)+a*b+f = x+a*b+(f+f) := by ring
       _ = _ := by rw [hf,add_zero]
theorem shear_character (u v m n : ZMod 2) :
    m*(u+v)+n*v = m*u+(m+n)*v := by ring
theorem shear_involution (a b : ZMod 2) : a+b+b=a := by
  have hb : b+b=0 := by
    calc b+b=2*b := by ring
         _=0 := by have h : (2:ZMod 2)=0 := by decide
                   rw [h,zero_mul]
  rw [add_assoc,hb,add_zero]
theorem phase_debt (p m f : Bool) :
    Bool.xor (Bool.xor p (m && f)) (m && f) = p := by
  cases p <;> cases m <;> cases f <;> decide
end GVQCC.TensorRank
#print axioms GVQCC.TensorRank.transpose_character
#print axioms GVQCC.TensorRank.product_order
#print axioms GVQCC.TensorRank.pivot_product
#print axioms GVQCC.TensorRank.shear_character
#print axioms GVQCC.TensorRank.shear_involution
#print axioms GVQCC.TensorRank.phase_debt
