import Mathlib

namespace GVQCC.GeneralRational316

/-- Padding by a power of X does not alter a residue at any nonzero
root: the numerator and the x-weighted derivative receive the same
nonzero factor. -/
theorem projective_padding {F : Type*} [Field F] (p d s : F) (hs : s ≠ 0) :
    (s*p)/(s*d) = p/d := by
  by_cases hd : d = 0
  · simp [hd]
  · field_simp [hs,hd]

theorem padding_derivative_at_root {R : Type*} [CommRing R]
    (h hp d dp : R) (hd : d = 0) : hp*d+h*dp = h*dp := by
  simp [hd]

/-- The two outputs share one dual-number multiplication. -/
theorem dual_product {R : Type*} [CommRing R] (a b u v eps : R)
    (he : eps^2=0) :
    (a+u*eps)*(b+v*eps)=a*b+(a*v+u*b)*eps := by
  calc
    _ = a*b+(a*v+u*b)*eps+(u*v)*eps^2 := by ring
    _ = _ := by rw [he,mul_zero,add_zero]

/-- Imaginary coefficient of a numerator times conjugate denominator.
Characteristic two cancels the two bv contributions. -/
theorem relative_trace_coefficient {R : Type*} [CommRing R]
    (a b u v : R) (h2 : (2:R)=0) :
    u*b+v*(a+b)+v*b=u*b+v*a := by
  calc
    _ = u*b+v*a+2*(v*b) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]

theorem norm_conjugate {R : Type*} [CommRing R]
    (a b t k : R) (ht : t^2=t+k) (h2 : (2:R)=0) :
    (a+b*t)*(a+b+b*t)=a^2+a*b+k*b^2 := by
  calc
    _ = a^2+a*b+b^2*(t^2-t)+2*(a*b*t+b^2*t) := by ring
    _ = _ := by rw [ht,add_sub_cancel_left,h2,zero_mul,add_zero]; ring

/-- Move the guard through a scalar division; zero-safe division is
important when arbitrary inputs contain repeated roots. -/
theorem guarded_division {F : Type*} [Field F] (p d : F) (g : Bool) :
    (if g then p else 0)/d = (if g then p/d else 0) := by
  cases g <;> simp

/-- A physical scratch word can be recomputed from still-live inputs
after its previous value has been erased, independent of intermediate
scratch usage. The two XOR calls restore the word. -/
theorem scratch_reuse (a m t : Bool) :
    ((t ^^ (a && m)) ^^ (a && m)) = t := by
  cases a <;> cases m <;> cases t <;> rfl

/-- Exact 42-term historical dual-number tensor, GF64 modulus 0x43. -/
def terms : List (Nat × Nat × Nat) :=
 [(1527,1527,660),(2578,2578,3037),(2864,2864,1056),(4069,4069,2377),
 (3783,3783,4093),(290,290,3433),(3543,3543,652),(1192,1192,3019),
 (3116,3116,1057),(2431,2431,2375),(507,507,4074),(2180,2180,3430),
 (589,589,2834),(756,756,185),(1996,1996,1809),(185,185,2987),
 (1409,1409,1960),(1336,1336,3258),(1005,1005,3731),(2766,2766,247),
 (336,336,1158),(2339,2339,3684),(701,701,1137),(2974,2974,2786),
 (3921,3921,2683),(3272,3272,3341),(1974,1974,1285),(921,921,1910),
 (2279,2279,2056),(2942,2942,627),(113,113,2604),(3442,3442,3714),
 (3626,3626,220),(3331,3331,1198),(3675,3675,3678),(856,856,1138),
 (235,235,1494),(2734,2734,961),(3146,3146,1614),(2629,2629,1559),
 (3233,3233,1423),(1764,1764,89)]
def mono : Nat → Nat
  | 0 => 1
  | n+1 => let v := mono n
           if v ≥ 32 then Nat.xor (2*v) 67 else 2*v
def basisExpected (i j : Nat) : Nat :=
  if i<6 && j<6 then mono (i+j)
  else if i<6 && j≥6 then 64*mono (i+j-6)
  else if i≥6 && j<6 then 64*mono (i+j-6)
  else 0
def tensorAt (i j : Nat) : Nat :=
  terms.foldl (fun z t => if t.1.testBit i && t.2.1.testBit j
    then Nat.xor z t.2.2 else z) 0
theorem exact_tensor_count : terms.length = 42 := rfl
theorem exact_tensor_basis : ∀ i j : Fin 12,
    tensorAt i.val j.val = basisExpected i.val j.val := by decide

/-- Correct static accounting: 42 shared products, 16 phase products,
6 guard transfers, and 11 root conjunctions per scan point. -/
theorem scan_paid : 4095*(42+16+6+11) = (307125:Nat) := by decide
theorem scan_width : 840+11+12+16 = (879:Nat) := by decide

end GVQCC.GeneralRational316
#print axioms GVQCC.GeneralRational316.projective_padding
#print axioms GVQCC.GeneralRational316.padding_derivative_at_root
#print axioms GVQCC.GeneralRational316.dual_product
#print axioms GVQCC.GeneralRational316.relative_trace_coefficient
#print axioms GVQCC.GeneralRational316.norm_conjugate
#print axioms GVQCC.GeneralRational316.guarded_division
#print axioms GVQCC.GeneralRational316.scratch_reuse
#print axioms GVQCC.GeneralRational316.exact_tensor_count
#print axioms GVQCC.GeneralRational316.exact_tensor_basis
#print axioms GVQCC.GeneralRational316.scan_paid
#print axioms GVQCC.GeneralRational316.scan_width
