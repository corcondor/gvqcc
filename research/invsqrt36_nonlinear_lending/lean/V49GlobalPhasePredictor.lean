import Std.Tactic
namespace GVQCC.V49

def z (b : Bool) : Int := if b then 1 else 0
def chi (b : Bool) : Int := if b then -1 else 1

theorem phase_adjoint (f p : Bool) (c : Int) :
    z f * c * chi p = c * z (Bool.xor f p) - c * z p := by
  cases f <;> cases p <;> simp [z, chi, Bool.xor] <;> omega

theorem phase_carry (a b : Bool) (c : Int) :
    c * (z a + z b) = c * z (Bool.xor a b) + (2*c)*z (a && b) := by
  cases a <;> cases b <;> simp [z, Bool.xor] <;> omega

theorem walsh_split (a b : Int) (s : Bool) :
    a + chi s * b = if s then a-b else a+b := by
  cases s <;> simp [chi] <;> omega

theorem parity_transport (a b da db : Bool) :
    Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
    Bool.xor (Bool.xor (a && db) (da && b)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem equal_phase_debt (m a b : Bool) (h : a=b) :
    Bool.xor (m && a) (m && b) = false := by
  subst b
  cases m <;> cases a <;> decide

def parity : List Bool → Bool
  | [] => false
  | b :: bs => Bool.xor b (parity bs)

theorem shared_product (a : Bool) (bs : List Bool) :
    parity (bs.map (fun b => a && b)) = (a && parity bs) := by
  induction bs with
  | nil => cases a <;> rfl
  | cons b bs ih =>
    simp only [List.map_cons, parity, ih]
    cases a <;> cases b <;> cases h : parity bs <;> decide

def abelL (c : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (m,d) :: xs => Bool.xor (m && Bool.xor c d) (abelL d xs)
def abelR (p c : Bool) : List (Bool × Bool) → Bool
  | [] => p && c
  | (m,d) :: xs => Bool.xor (Bool.xor p m && c) (abelR m d xs)

theorem abel_step (p c m d v : Bool) :
    Bool.xor (p && c) (Bool.xor (m && Bool.xor c d) v) =
    Bool.xor (Bool.xor p m && c) (Bool.xor (m && d) v) := by
  cases p <;> cases c <;> cases m <;> cases d <;> cases v <;> decide

theorem abel_multi (xs : List (Bool × Bool)) (p c : Bool) :
    Bool.xor (p && c) (abelL c xs) = abelR p c xs := by
  induction xs generalizing p c with
  | nil => cases p <;> cases c <;> rfl
  | cons hd tl ih =>
    rcases hd with ⟨m,d⟩
    simp only [abelL, abelR]
    rw [← ih m d]
    exact abel_step p c m d (abelL d tl)

theorem resource_accounting :
    36152 - 274 = 35878 ∧ 4194303 - 18787 = 4175516 ∧
    33 - 1 = 32 ∧ 192 - 15 = 177 := by decide

end GVQCC.V49
