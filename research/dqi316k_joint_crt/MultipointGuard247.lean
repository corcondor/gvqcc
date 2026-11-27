import Init
import Std

namespace GVQCC.MultipointGuard247

/-- Conjugating one product-target addition by a linear shear distributes
    it to the other targets while preserving their previous contents. -/
theorem output_shear {A : Type} (add : A â A â A) (zero : A) (scale : A â A)
    (assoc : â x y z, add (add x y) z = add x (add y z))
    (self : â x, add x x = zero) (id : â x, add zero x = x)
    (lin : â x y, scale (add x y) = add (scale x) (scale y))
    (out pivot delta : A) :
    add (add out (scale pivot)) (scale (add pivot delta)) =
      add out (scale delta) := by
  rw [lin, assoc, â assoc (scale pivot) (scale pivot) (scale delta), self, id]

/-- Source frame correction in characteristic two. The old pivot may be
    eliminated from one linear form using the new pivot coordinate. -/
theorem source_correction {A : Type} (add : A â A â A) (zero : A)
    (scale : A â A)
    (assoc : â x y z, add (add x y) z = add x (add y z))
    (self : â x, add x x = zero) (id : â x, add zero x = x)
    (lin : â x y, scale (add x y) = add (scale x) (scale y))
    (out pivot tail : A) :
    add (add out (scale pivot)) (scale (add pivot tail)) =
      add out (scale tail) := output_shear add zero scale assoc self id lin out pivot tail

/-- Multipoint evaluation must use a Frobenius preimage of each weight.
    This lemma states the exact compatibility with the field automorphism. -/
theorem frobenius_weight {A : Type} (mul : A â A â A) (frob inv : A â A)
    (hm : â x y, frob (mul x y) = mul (frob x) (frob y))
    (hi : â x, frob (inv x) = x) (a c : A) :
    frob (mul (inv c) a) = mul c (frob a) := by rw [hm, hi]

/-- A basis-pair certificate yields a correct accumulated bilinear term:
    proof obligation is the field tensor, not individual sampled inputs. -/
theorem coefficient_transport {A : Type} (mul : A â A â A)
    (a b c expected : A) (hm : â x y z, mul (mul x y) z = mul x (mul y z))
    (h : c = expected) : mul (mul a b) c = mul a (mul b expected) := by rw [hm,h]

/-- Independent corrections to a phase bit cancel in any order. -/
theorem phase_cancel (x m : Bool) :
    Bool.xor (Bool.xor x m) m = x := by cases x <;> cases m <;> decide

#print axioms output_shear
#print axioms source_correction
#print axioms frobenius_weight
#print axioms coefficient_transport
#print axioms phase_cancel
end GVQCC.MultipointGuard247
