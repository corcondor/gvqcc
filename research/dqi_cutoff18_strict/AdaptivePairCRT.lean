import Mathlib

namespace GVQCC.AdaptivePairCRT
open Polynomial

/-- The first skipped node becomes a legal pivot with quotient zero immediately
after transport through any distinct selected node. -/
theorem skipped_node_forced_zero {F : Type*} [Field F]
    (n d h g : F) (hn : n = 0) (hd : d ≠ 0) :
    (d+h*n) ≠ 0 ∧ g*n = 0 ∧ (g*n)/(d+h*n) = 0 := by
  simp [hn, hd]

/-- The zero branch of the in-place scaling also restores the temporary word. -/
theorem reciprocal_scale_restore {F : Type*} [Field F] (a n : F)
    (hz : n = 0 → a = 0) : (a*n⁻¹)*n = a := by
  by_cases hn : n = 0
  · simp [hn, hz hn]
  · rw [mul_assoc, inv_mul_cancel₀ hn, mul_one]

/-- Conjugation in the quadratic characteristic-two extension preserves norm. -/
theorem conjugate_norm {R : Type*} [CommRing R] (a b k : R)
    (htwo : (2 : R) = 0) :
    (a+b)^2+(a+b)*b+k*b^2 = a^2+a*b+k*b^2 := by
  calc
    _ = a^2+a*b+k*b^2+2*(a*b+b^2) := by ring
    _ = _ := by rw [htwo, zero_mul, add_zero]

theorem scaled_norm {R : Type*} [CommRing R] (a b k h : R) :
    (a*h)^2+(a*h)*(b*h)+k*(b*h)^2 =
      (a^2+a*b+k*b^2)*h^2 := by ring

theorem norm_inverse_cleanup {R : Type*} [CommRing R] (n h : R)
    (hinv : n*h=1) : n*h^2=h := by
  calc
    _ = (n*h)*h := by ring
    _ = h := by rw [hinv, one_mul]

/-- The entire all-pole numerator has only a scalar degree of freedom. -/
theorem allpole_degree {F : Type*} [Field F] (G N R : Polynomial F)
    (hg : G.natDegree=34) (hn : N.natDegree≤34) (hn0 : N ≠ 0)
    (he : N=G*R) : R.natDegree=0 := by
  have hg0 : G ≠ 0 := by
    intro hz
    rw [hz] at hg
    simp at hg
  have hr0 : R ≠ 0 := by
    intro hz
    rw [hz, mul_zero] at he
    exact hn0 he
  have hm := Polynomial.natDegree_mul hg0 hr0
  rw [← he, hg] at hm
  omega

/-- Applies directly in the quotient ring K[X]/(M): B*D=c. -/
theorem crt_inverse_scaled {R : Type*} [CommRing R]
    (B D c ic : R) (hc : c*ic=1) (h : B*D=c) : B*(D*ic)=1 := by
  rw [← mul_assoc, h, hc]

theorem crt_inverse_unique {R : Type*} [CommRing R]
    (B X Y : R) (hx : B*X=1) (hy : B*Y=1) : X=Y := by
  calc
    X = X*1 := by simp
    _ = X*(B*Y) := by rw [hy]
    _ = (B*X)*Y := by ring
    _ = Y := by rw [hx, one_mul]

theorem crt_representative_unique {F : Type*} [Field F]
    (P Q : Polynomial F) (s : Finset F) (hd : (P-Q).natDegree < s.card)
    (he : ∀ x ∈ s, P.eval x=Q.eval x) : P=Q := by
  apply sub_eq_zero.mp
  apply Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' (P-Q) s _ hd
  intro x hx
  simp [he x hx]

theorem scaled_amplitude {F : Type*} [Field F] (x M d c : F)
    (hx : x≠0) (hm : M≠0) (hd : d≠0) (hc : c≠0) :
    (x*M*(d/c))⁻¹ = c/(x*M*d) := by
  field_simp [hx, hm, hd, hc] <;> ring

/-- Let a=F_l, b=F_(l+1). Valid ranks for a history of consumed length l
occupy [a+b-1,a+2b-1). A one-slot macro is in the first subinterval. -/
theorem history_normal (a b H : ℕ) (hb : 0<b)
    (hlo : a+b-1≤H) (hhi : H<a+2*b-1) :
    a+2*b-1≤H+b ∧ H+b<a+3*b-1 ∧ (H+b)-b=H := by omega

/-- A two-slot jump macro occupies the disjoint second subinterval. -/
theorem history_jump (a b H : ℕ) (hb : 0<b)
    (hlo : a+b-1≤H) (hhi : H<a+2*b-1) :
    3*a+4*b-1≤H+(2*a+3*b) ∧
    H+(2*a+3*b)<3*a+5*b-1 ∧ (H+(2*a+3*b))-(2*a+3*b)=H := by omega

/-- An output rank of length l+2 is uniquely distinguished as a final
one-slot or two-slot macro by the interval boundary. -/
theorem history_last_partition (a b H : ℕ) (hb : 0<b)
    (hlo : 2*a+3*b-1≤H) (hhi : H<3*a+5*b-1) :
    (H<3*a+4*b-1 ∧ a+2*b-1≤H-(a+b) ∧
      H-(a+b)<2*a+3*b-1) ∨
    (3*a+4*b-1≤H ∧ a+b-1≤H-(2*a+3*b) ∧
      H-(2*a+3*b)<a+2*b-1) := by omega

def fibPair : ℕ → ℕ × ℕ
  | 0 => (0,1)
  | n+1 => let p := fibPair n; (p.2,p.1+p.2)

def historyBound (n : ℕ) : ℕ :=
  (fibPair n).1+2*(fibPair n).2-1

theorem history_capacity_35 : historyBound 35=39088168 := by decide

theorem history_all_35 : ∀ n : Fin 36, historyBound n.val≤39088168 := by decide

theorem history_fits_26 (l H : ℕ) (hl : l≤35) (hh : H<historyBound l) :
    H<2^26 := by
  have h := history_all_35 ⟨l, by omega⟩
  change historyBound l≤39088168 at h
  change H<67108864
  omega

end GVQCC.AdaptivePairCRT
#print axioms GVQCC.AdaptivePairCRT.skipped_node_forced_zero
#print axioms GVQCC.AdaptivePairCRT.reciprocal_scale_restore
#print axioms GVQCC.AdaptivePairCRT.conjugate_norm
#print axioms GVQCC.AdaptivePairCRT.scaled_norm
#print axioms GVQCC.AdaptivePairCRT.norm_inverse_cleanup
#print axioms GVQCC.AdaptivePairCRT.allpole_degree
#print axioms GVQCC.AdaptivePairCRT.crt_inverse_scaled
#print axioms GVQCC.AdaptivePairCRT.crt_inverse_unique
#print axioms GVQCC.AdaptivePairCRT.crt_representative_unique
#print axioms GVQCC.AdaptivePairCRT.scaled_amplitude
#print axioms GVQCC.AdaptivePairCRT.history_normal
#print axioms GVQCC.AdaptivePairCRT.history_jump
#print axioms GVQCC.AdaptivePairCRT.history_last_partition
#print axioms GVQCC.AdaptivePairCRT.history_capacity_35
#print axioms GVQCC.AdaptivePairCRT.history_all_35
#print axioms GVQCC.AdaptivePairCRT.history_fits_26
