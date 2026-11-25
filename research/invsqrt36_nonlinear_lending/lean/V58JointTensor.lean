import Init
namespace GVQCC.V58
def bx (a b : Bool) := Bool.xor a b
def bit (a : Bool) : Nat := if a then 1 else 0
def careLoad (a b c h k : Bool) : Bool :=
  bx (bx (bx a b) c) (bx (h && bx b c) (k && bx a c))
theorem care10 (a b c : Bool) : careLoad a b c true false = a := by
  cases a <;> cases b <;> cases c <;> decide
theorem care01 (a b c : Bool) : careLoad a b c false true = b := by
  cases a <;> cases b <;> cases c <;> decide
theorem care11 (a b c : Bool) : careLoad a b c true true = c := by
  cases a <;> cases b <;> cases c <;> decide
def maj (a b c : Bool) := bx b (bx a b && bx c b)
theorem compressor (a b c : Bool) :
    bit a + bit b + bit c = bit (bx (bx a b) c) + 2 * bit (maj a b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem coefficient_shared (p a b c : Bool) :
    bit (p && a) + bit (p && b) + bit (p && c) =
    bit (p && bx (bx a b) c) + 2 * bit (p && maj a b c) := by
  cases p <;> cases a <;> cases b <;> cases c <;> decide
theorem hmr_split (m a b h k : Bool) :
    bx (m && bx a (bx (h && b) k)) (bx (m && a) (bx (m && h && b) (m && k))) = false := by
  cases m <;> cases a <;> cases b <;> cases h <;> cases k <;> decide
end GVQCC.V58