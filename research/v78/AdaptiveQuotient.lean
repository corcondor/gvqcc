import Std
import Lean
namespace GVQCC.V78

def chi (b : Bool) : Int := if b then -1 else 1

def indicator (b : Bool) : Int := if b then 1 else 0

theorem signedCosetExchange (s v h : Bool) (a : Int) :
    a * chi (s ^^ v) * indicator (v == h) =
      chi h * a * chi s * indicator (v == h) := by
  cases s <;> cases v <;> cases h <;>
    simp [chi, indicator, Bool.xor, Int.neg_mul, Int.mul_neg]

theorem sharedProduct (a b c : Bool) :
    (a && (b ^^ c)) = ((a && b) ^^ (a && c)) := by
  cases a <;> cases b <;> cases c <;> decide

theorem discreteParts (a a' b b' : Int) :
    (a' - a) * b' + a * (b' - b) = a' * b' - a * b := by
  simp only [Int.sub_mul, Int.mul_sub]
  omega

theorem exchangeDelta (a b da db : Bool) :
    ((a ^^ da) && (b ^^ db)) ^^ (a && b) =
      (((a && db) ^^ (da && b)) ^^ (da && db)) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

-- The abstract characteristic-two ring law. Applies to GF(2^12)[X]
-- and its truncated polynomial rings once their ring laws are supplied.
theorem char2Square {A : Type} (add mul : A → A → A) (zero : A)
    (left : ∀ a b c, mul a (add b c) = add (mul a b) (mul a c))
    (right : ∀ a b c, mul (add a b) c = add (mul a c) (mul b c))
    (mc : ∀ a b, mul a b = mul b a)
    (aa : ∀ a b c, add (add a b) c = add a (add b c))
    (self : ∀ a, add a a = zero)
    (za : ∀ a, add zero a = a)
    (a b : A) :
    mul (add a b) (add a b) = add (mul a a) (mul b b) := by
  calc
    mul (add a b) (add a b) =
      add (add (mul a a) (mul b a)) (add (mul a b) (mul b b)) := by
        rw [left, right, right]
    _ = add (mul a a) (add (mul a b) (add (mul a b) (mul b b))) := by
        rw [mc b a, aa]
    _ = add (mul a a) (add (add (mul a b) (mul a b)) (mul b b)) := by
        rw [aa (mul a b) (mul a b) (mul b b)]
    _ = add (mul a a) (mul b b) := by rw [self, za]

theorem reciprocalNewton {A : Type} (add mul : A → A → A) (one : A)
    (ma : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (mc : ∀ a b, mul a b = mul b a)
    (unit : mul one one = one)
    (sq : ∀ a b, mul (add a b) (add a b) = add (mul a a) (mul b b))
    (p r e : A) (h : mul p r = add one e) :
    mul p (mul p (mul r r)) = add one (mul e e) := by
  calc
    mul p (mul p (mul r r)) = mul p (mul (mul p r) r) := by rw [ma p r r]
    _ = mul p (mul r (mul p r)) := by rw [mc (mul p r) r]
    _ = mul (mul p r) (mul p r) := (ma p r (mul p r)).symm
    _ = add one (mul e e) := by rw [h, sq, unit]

-- Orthogonal two-column symmetry as an integer polynomial identity.
-- This does not certify floating-point FeMoCo numerical optimization.
theorem gramRotation (a b x y u v : Int) :
    (a*x+b*y)*(a*u+b*v) + ((-b)*x+a*y)*((-b)*u+a*v) =
      (a*a+b*b)*(x*u+y*v) := by
  simp only [Int.mul_add, Int.add_mul, Int.neg_mul, Int.mul_neg, Int.neg_neg]
  simp only [Int.mul_assoc, Int.mul_left_comm, Int.mul_comm]
  omega

end GVQCC.V78
