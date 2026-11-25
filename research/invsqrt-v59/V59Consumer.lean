import Std.Tactic
namespace GVQCC.V59
def bit (b : Bool) : Int := if b then 1 else 0
def maj (a b c : Bool) : Bool := (a && b) || (a && c) || (b && c)
def parity (a b c : Bool) : Bool := Bool.xor (Bool.xor a b) c
theorem booth_local_correction (a b c : Bool) (u : Int) :
    (if bit a + bit b - 2 * bit c = 2 then u else
      if bit a + bit b - 2 * bit c = -2 then -u else 0) =
      u * (bit (maj a b c) - bit c) := by
  cases a <;> cases b <;> cases c <;> simp [bit, maj] <;> omega
theorem count3 (a b c : Bool) :
    bit a + bit b + bit c = bit (parity a b c) + 2 * bit (maj a b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem shared_count3 (a b c d : Bool) :
    bit d * bit a + bit d * bit b + bit d * bit c =
      bit d * bit (parity a b c) + 2 * (bit d * bit (maj a b c)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem signed_offset (x o : Int) : (x + o) - o = x := by omega
theorem savings : 742 - 676 = (66 : Nat) ∧ 676 - 577 = 99 := by decide
end GVQCC.V59
