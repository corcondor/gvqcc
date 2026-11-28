import Mathlib
namespace GVQCC.SchurGauge
section Ring
variable {R : Type*} [CommRing R]

theorem gauge_bracket (a b c d r : R) (h2 : (2 : R) = 0) :
    a*(d+r*c)+(b+r*a)*c = a*d+b*c := by
  calc
    _ = a*d+b*c+2*(r*a*c) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem gauge_restore (a b r : R) (h2 : (2 : R) = 0) :
    (b+r*a)+r*a = b := by
  calc
    _ = b+2*(r*a) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem pair_left (x t s v : R) (h2 : (2 : R) = 0) :
    (x+s)^2*v+(t+s)*(x+s)*v = (x+t)*(x+s)*v := by
  calc
    _ = (x+t)*(x+s)*v+2*(s*(x+s)*v) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem pair_right (x t s v : R) (h2 : (2 : R) = 0) :
    (x+t)^2*v+(t+s)*(x+t)*v = (x+t)*(x+s)*v := by
  calc
    _ = (x+t)*(x+s)*v+2*(t*(x+t)*v) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem one_restore (a b r alpha delta ap bp : R)
    (h2 : (2 : R) = 0) (ha : delta*ap = a+alpha*bp)
    (hb : delta*bp = b+r*a) :
    delta*ap+alpha*bp = a ∧ delta*bp+r*a = b := by
  constructor
  · rw [ha]; exact gauge_restore bp a alpha h2
  · rw [hb]; exact gauge_restore a b r h2

theorem shared_rhs_restore (a b u v l : R) (h2 : (2 : R) = 0) :
    ((a+l*u)+l*u, (b+l*v)+l*v) = (a,b) := by
  rw [gauge_restore u a l h2, gauge_restore v b l h2]

end Ring

theorem partner_forces {F : Type*} [Field F] (c k : F)
    (hc : c ≠ 0) (hk : k ≠ 0) : c*c/k ≠ 0 :=
  div_ne_zero (mul_ne_zero hc hc) hk

theorem no_wrap (a b k r : ℕ) (ha : a < k) (hb : b < r)
    (hw : k ≤ a+b) : a+b-k < r-1 := by omega

def paths : ℕ → ℕ
  | 0 => 1
  | 1 => 1
  | n+2 => paths (n+1) + 2*(n+1)*paths n

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem path_count : paths 17 = 25330978113 := by decide

theorem history_fits : paths 17 ≤ 2^35 := by rw [path_count]; decide
theorem history_bits_needed : 2^34 < paths 17 := by rw [path_count]; decide
theorem storage_sum : 70*12+12+12+35 = 899 := by decide

#print axioms gauge_bracket
#print axioms gauge_restore
#print axioms pair_left
#print axioms pair_right
#print axioms one_restore
#print axioms shared_rhs_restore
#print axioms partner_forces
#print axioms no_wrap
#print axioms path_count
#print axioms history_fits
#print axioms history_bits_needed
#print axioms storage_sum
end GVQCC.SchurGauge
