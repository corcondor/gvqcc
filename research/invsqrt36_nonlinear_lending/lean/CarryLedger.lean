import Init

/-! Algebraic core for the shared-operand carry chain and the HMR phase ledger.
This verifies the local Boolean identities, not the numerical approximation,
KMB serialization or the complete inverse-square-root oracle. -/
namespace GVQCC.CarryLedger

def bx (a b : Bool) : Bool := Bool.xor a b

def carry (a b c : Bool) : Bool :=
  bx ((bx a c) && (bx b c)) c

def sumBit (a b c : Bool) : Bool := bx (bx a b) c

-- MAJ: store the new carry in an existing operand, with no fresh ancilla.
def maj (a b c : Bool) : Bool × Bool × Bool :=
  let b1 := bx b a
  let c1 := bx c a
  (bx a (b1 && c1), b1, c1)

def unmaj (a b c : Bool) : Bool × Bool × Bool :=
  let a0 := bx a (b && c)
  (a0, bx b a0, bx c a0)

def restoreAndSum (a b c : Bool) : Bool × Bool × Bool :=
  let p := unmaj a b c
  (p.1, sumBit p.1 p.2.1 p.2.2, p.2.2)

theorem majority_same (a b c : Bool) :
    (maj a b c).1 = carry a b c := by
  cases a <;> cases b <;> cases c <;> decide

theorem majority_symmetric (a b c : Bool) :
    (maj b a c).1 = carry a b c := by
  cases a <;> cases b <;> cases c <;> decide

theorem inverse_maj (a b c : Bool) :
    unmaj (maj a b c).1 (maj a b c).2.1 (maj a b c).2.2 =
      (a,b,c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem reverse_add (a b c : Bool) :
    restoreAndSum (maj a b c).1 (maj a b c).2.1 (maj a b c).2.2 =
      (a,sumBit a b c,c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem reverse_add_swap (a b c : Bool) :
    let p := maj b a c
    let r := unmaj p.1 p.2.1 p.2.2
    (r.2.1, sumBit r.2.1 r.1 r.2.2, r.2.2) = (a,sumBit a b c,c) := by
  cases a <;> cases b <;> cases c <;> decide

-- A full two-stage carry chain can move the central carry onto a
-- different operand at each stage; reverse reconstruction restores both.
theorem two_stage_carry (a b c d e : Bool) :
    (maj d e (maj a b c).1).1 = carry d e (carry a b c) := by
  rw [majority_same, majority_same]

-- Boolean Shannon expansion used by the exact transcript ANF ledger.
theorem shannon_anf (m lo hi : Bool) :
    (if m then hi else lo) = bx lo (m && bx lo hi) := by
  cases m <;> cases lo <;> cases hi <;> decide

theorem phase_cancel (p h m : Bool) :
    bx (bx p (h && m)) (h && m) = p := by
  cases p <;> cases h <;> cases m <;> decide

theorem zero_coefficient (p m h : Bool) (hz : h = false) :
    bx p (m && h) = p := by
  subst h
  cases p <;> cases m <;> decide

end GVQCC.CarryLedger
