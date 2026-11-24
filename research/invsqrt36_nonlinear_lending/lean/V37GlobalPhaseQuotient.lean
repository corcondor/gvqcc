import Std
namespace V37

-- Difference transport and the telescoping of consecutive debts.
theorem transport (m x y z : Bool) :
    Bool.xor (m && Bool.xor x y) (m && Bool.xor y z) =
      (m && Bool.xor x z) := by
  cases m <;> cases x <;> cases y <;> cases z <;> decide

theorem parity_roundtrip (x y : Bool) :
    Bool.xor (Bool.xor x y) y = x := by
  cases x <;> cases y <;> decide

-- A butterfly is inverted by the same butterfly, up to a factor of two.
theorem butterfly_inverse (a b : Int) :
    (a+b)+(a-b)=2*a ∧ (a+b)-(a-b)=2*b := by
  omega

def bitAngle (p : Bool) (a : Int) : Int := if p then a else 0
def signedAngle (p : Bool) (a : Int) : Int := if p then -a else a

theorem parity_angle (p : Bool) (a : Int) :
    2 * bitAngle p a = a - signedAngle p a := by
  cases p <;> simp [bitAngle, signedAngle] <;> omega

-- Adding two sign bits differs from XOR only by an integer full turn.
theorem sign_carry (p q : Bool) (h : Int) :
    bitAngle p h + bitAngle q h =
      bitAngle (Bool.xor p q) h + bitAngle (p && q) (2*h) := by
  cases p <;> cases q <;> simp [bitAngle, Bool.xor] <;> omega

def sumAngles : List (Bool × Int) → Int
  | [] => 0
  | (p,a)::xs => a + sumAngles xs
def sumSigned : List (Bool × Int) → Int
  | [] => 0
  | (p,a)::xs => signedAngle p a + sumSigned xs
def sumParity : List (Bool × Int) → Int
  | [] => 0
  | (p,a)::xs => bitAngle p a + sumParity xs

-- Integer parity expansion: the sum of coefficients minus the Walsh sum
-- is exactly twice the parity phase. No floating point or rounding.
theorem parity_sum (xs : List (Bool × Int)) :
    2 * sumParity xs = sumAngles xs - sumSigned xs := by
  induction xs with
  | nil => simp [sumParity, sumAngles, sumSigned]
  | cons x xs ih =>
    obtain ⟨p,a⟩ := x
    simp only [sumParity, sumAngles, sumSigned]
    have h := parity_angle p a
    omega

end V37
