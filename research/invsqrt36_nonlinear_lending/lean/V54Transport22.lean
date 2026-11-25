import Std.Tactic
namespace GVQCC.V54

-- A change of prefix and a change of direction can be implemented as
-- two rank-one toggles; the old tensor is never materialized separately.
theorem tensor_transport (v w f g : Bool) :
    Bool.xor (v && f)
      (Bool.xor (Bool.xor v w && f) (w && Bool.xor f g)) =
      (w && g) := by
  cases v <;> cases w <;> cases f <;> cases g <;> decide

theorem parity_fanout (x y f : Bool) :
    Bool.xor (Bool.xor y x) (Bool.xor x f) = Bool.xor y f := by
  cases x <;> cases y <;> cases f <;> decide

theorem borrowed_commutator (d f g : Bool) :
    Bool.xor ((Bool.xor d f) && g) (d && g) = (f && g) := by
  cases d <;> cases f <;> cases g <;> decide

def bit (b : Bool) : Int := if b then 1 else 0
def character (b : Bool) : Int := if b then -1 else 1

theorem phase_difference (r f : Bool) :
    bit (Bool.xor r f) - bit r = bit f * character r := by
  cases r <;> cases f <;> decide

-- Integer sibling transform. Division by two is performed only when exact.
theorem sibling_contract (a b : Int) (s : Bool) :
    2 * (if s then b else a) = (a+b) + (a-b) * character s := by
  cases s <;> simp [character] <;> omega

theorem echo (a b g : Bool) :
    bit (Bool.xor a g) + bit (Bool.xor b g) - bit a - bit b =
      (if g then 2 - 2 * (bit a + bit b) else 0) := by
  cases a <;> cases b <;> cases g <;> decide

-- The legal domain excludes the 11 high-bit sector.
theorem legal_echo (a b g : Bool) (h : (a && b) = false) :
    bit (Bool.xor a g) + bit (Bool.xor b g) - bit a - bit b =
      2 * bit (!a && !b && g) := by
  cases a <;> cases b <;> cases g <;> simp_all [bit]

theorem rank_embedding_injective {X C R : Type}
    (code : X → C) (rank : X → R)
    (h : ∀ x y, code x = code y → rank x = rank y → x = y) :
    Function.Injective (fun x => (code x, rank x)) := by
  intro x y he
  exact h x y (congrArg Prod.fst he) (congrArg Prod.snd he)

theorem arithmetic_receipts :
    55606 - 8152 = 47454 ∧ 115245 - 53868 = 61377 ∧
    13453 - 11047 = 2406 ∧ 254 ≤ 2^8 ∧ 1912 ≤ 2^11 ∧
    2^22 - 3133452 = 1060852 ∧ 3133452 < 3 * 2^20 := by decide
end GVQCC.V54
