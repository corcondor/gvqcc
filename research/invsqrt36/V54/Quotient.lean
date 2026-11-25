import Std.Tactic

namespace V54
def bit (b : Bool) : Int := if b then 1 else 0
def sign (b : Bool) : Int := if b then -1 else 1

-- Exact finite Walsh projector, valid as an integer identity before
-- conversion to modular fixed-point angle arithmetic.
theorem selector_weight (s t a b f : Bool) :
    8 * bit ((!(s ^^ a)) && (!(t ^^ b)) && f) =
      (1 + sign (s ^^ a)) * (1 + sign (t ^^ b)) * (1 - sign f) := by
  cases s <;> cases t <;> cases a <;> cases b <;> cases f <;> decide

theorem character_mul (a b : Bool) :
    sign (a ^^ b) = sign a * sign b := by
  cases a <;> cases b <;> decide

-- A relation q*d=r determines the omitted coordinate when d=1;
-- exceptional cases use the independently certified fallback.
theorem cofactor_glue (q d r fallback : Bool)
    (h : (q && d) = r) (he : d = false -> fallback = q) :
    (if d then r else fallback) = q := by
  cases d
  · exact he rfl
  · simpa using h.symm

-- Nonlinear transport on a retained chart: no linearity assumption.
theorem transport {A B C : Type} (encode : A -> B) (decode : B -> A)
    (f : A -> C) (x : A) (h : decode (encode x) = x) :
    f (decode (encode x)) = f x := by rw [h]

-- A clean presampled measurement contributes no input-dependent sign.
theorem clean_phase (m : Bool) : (false && m) = false := by cases m <;> decide

end V54
