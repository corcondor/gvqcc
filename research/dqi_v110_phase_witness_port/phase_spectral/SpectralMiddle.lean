import Lean

namespace GVQCC.SpectralMiddle

-- Low source has degree < m and the kernel has degree < L.
-- Overflow in cyclic convolution wraps only below m-1.
theorem no_middle_wrap (m L e j : Nat)
    (_hm : 0 < m) (_hml : m ≤ L + 1)
    (he : e + 2 ≤ L + m)
    (hj : m ≤ j + 1) (hjL : j < L)
    (hmod : e % L = j) : e = j := by
  by_cases h : e < L
  · rwa [Nat.mod_eq_of_lt h] at hmod
  · have hge : L ≤ e := Nat.le_of_not_gt h
    have hsmall : e - L < L := by omega
    rw [Nat.mod_eq_sub_mod hge, Nat.mod_eq_of_lt hsmall] at hmod
    omega

theorem parity_reindex (i j u v r : Nat)
    (hr : r ≤ 1) (hi : i = 2*u+r)
    (hj : j = 2*v+(1-r)) (h : i < j) :
    j - i - 1 = 2 * (v-u-r) := by
  omega

theorem retained_shear_transport (x l old new : Bool) :
    Bool.xor (Bool.xor x (old && l)) ((Bool.xor old new) && l) =
      Bool.xor x (new && l) := by
  cases x <;> cases l <;> cases old <;> cases new <;> decide

#print axioms no_middle_wrap
#print axioms parity_reindex
#print axioms retained_shear_transport
end GVQCC.SpectralMiddle
