import Init

/-! Local carry and guarded measurement-debt schedule for the Family-C
two-clean-wire inverse adder. Abstract Boolean proof, not whole-KMB refinement. -/
namespace GVQCC.SharedGhost
def bx (a b : Bool) : Bool := Bool.xor a b
def step (a s c : Bool) : Bool := bx c (bx a c && bx a s)

/-- Two steps of the sum-coordinate carry recurrence can be paid with
a single cubic phase and Clifford phases, using the same live anchor. -/
theorem two_hop (a0 s0 a1 s1 c : Bool) :
    step a1 s1 (step a0 s0 c) =
      let x := bx a0 c
      let y := bx a0 s0
      let z := bx a1 s1
      bx (bx (bx c (x && y)) (bx a1 c && z)) (x && y && z) := by
  cases a0 <;> cases s0 <;> cases a1 <;> cases s1 <;> cases c <;> decide

def ga (m2 m3 m4 m5 : Bool) := m2 || m3 || m4 || m5
def gb (m3 m4 m5 : Bool) := m3 || m4 || m5
def g4 (m4 m5 : Bool) := m4 && !m5
def g45 (m4 m5 : Bool) := m4 && m5
def gb0 (m3 m4 m5 : Bool) := bx (gb m3 m4 m5) m5
def g2 (m5 mr : Bool) := m5 && mr

theorem or_shared (a b : Bool) : (a || b) = bx a (b && !a) := by
  cases a <;> cases b <;> decide

theorem split4 (m4 m5 : Bool) :
    bx (g4 m4 m5) (g45 m4 m5) = m4 ∧
    !(g4 m4 m5 && g45 m4 m5) = true := by
  cases m4 <;> cases m5 <;> decide

/-- Every activated reconstruction or correction has its predecessor
available, and the two disjoint exit branches have identical zero slots. -/
theorem guard_schedule :
    ∀ m2 m3 m4 m5 mr : Bool,
      let a := ga m2 m3 m4 m5
      let b := gb m3 m4 m5
      let exit := gb0 m3 m4 m5
      let repair := g2 m5 mr
      ((!m2 || a) && (!b || a) && (!m3 || b) &&
        (!(g4 m4 m5) || b) && (!exit || b) &&
        (bx b exit == m5) && (!m5 || a) &&
        (!(g45 m4 m5) || m5) && (!repair || m5)) = true := by decide

/-- Merged clearing of slot A uses ga once, instead of two separate
measurement-conditioned inverse blocks. -/
theorem merged_clear (m2 m3 m4 m5 : Bool) :
    let a := ga m2 m3 m4 m5
    bx (bx a (a && !m5)) m5 = bx a a := by
  cases m2 <;> cases m3 <;> cases m4 <;> cases m5 <;> decide

def debt (c2 c3 c4 c5 m2 m3 m4 m5 : Bool) :=
  bx (bx (m2 && c2) (m3 && c3)) (bx (m4 && c4) (m5 && c5))

def corrections (c2 c3 c4 c5 m2 m3 m4 m5 mr : Bool) :=
  bx (bx (bx (m2 && c2) (m3 && c3))
          (bx (g4 m4 m5 && c4) (g45 m4 m5 && c4)))
     (bx (m5 && c5) (g2 m5 mr && c2))

/-- All 512 carry/measurement combinations, including the second ghost
on a slot known to be zero on the inactive branch. -/
theorem all_phase_debts :
    ∀ c2 c3 c4 c5 m2 m3 m4 m5 mr : Bool,
      bx (bx (debt c2 c3 c4 c5 m2 m3 m4 m5) (g2 m5 mr && c2))
         (corrections c2 c3 c4 c5 m2 m3 m4 m5 mr) = false := by decide

/-- Unconditional measurement of a conditionally zero slot has the same
relative phase as the guarded measurement when correction uses the guard. -/
theorem zero_slot_measure (g c m : Bool) :
    (m && (g && c)) = ((g && m) && c) := by
  cases g <;> cases c <;> cases m <;> decide

def count (m2 m3 m4 m5 mr : Bool) : Nat :=
  7 + (if ga m2 m3 m4 m5 then 1 else 0) +
      (if gb m3 m4 m5 then 1 else 0) +
      (if m5 then 2 else 0) +
      (if g4 m4 m5 then 1 else 0) +
      (if g2 m5 mr then 1 else 0)

def ncost (n : Nat) := count (n.testBit 0) (n.testBit 1)
    (n.testBit 2) (n.testBit 3) (n.testBit 4)

/-- Uniform independent ghost bits, with the last bit irrelevant if m5=0:
exact expected cost 330/32 = 10.3125. -/
theorem expected_numerator : ((List.range 32).map ncost).foldl Nat.add 0 = 330 := by decide

end GVQCC.SharedGhost

#print axioms GVQCC.SharedGhost.two_hop
#print axioms GVQCC.SharedGhost.or_shared
#print axioms GVQCC.SharedGhost.split4
#print axioms GVQCC.SharedGhost.guard_schedule
#print axioms GVQCC.SharedGhost.merged_clear
#print axioms GVQCC.SharedGhost.all_phase_debts
#print axioms GVQCC.SharedGhost.zero_slot_measure
#print axioms GVQCC.SharedGhost.expected_numerator
