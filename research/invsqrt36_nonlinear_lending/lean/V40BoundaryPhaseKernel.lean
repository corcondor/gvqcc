import Std
namespace V40
def bx (a b : Bool) : Bool := Bool.xor a b

-- A product can be consumed in a transported carry frame without rebuilding c.
theorem carry_mux (a b c : Bool) :
    bx (a && b) c = bx (bx a c && b) (!b && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem carry_observation (a b c : Bool) :
    (bx (a && b) c && b) = (bx a c && b) := by
  cases a <;> cases b <;> cases c <;> decide

-- Substitution into a quadratic relation.
theorem quadratic_transport (a b d e : Bool) :
    (bx a d && bx b e) =
      bx (bx (a && b) (a && e)) (bx (d && b) (d && e)) := by
  cases a <;> cases b <;> cases d <;> cases e <;> decide

-- Weighted discrete Leibniz rule, hence summation by parts over GF(2).
theorem abel_step (u v u' v' : Bool) :
    bx (u && v) (u' && v') =
      bx (u && bx v v') (bx u u' && v') := by
  cases u <;> cases v <;> cases u' <;> cases v' <;> decide

theorem debt_telescope (m a b c : Bool) :
    bx (m && bx a b) (m && bx b c) = (m && bx a c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide

theorem xor_shuffle (a b c d : Bool) :
    bx (bx a b) (bx c d) = bx (bx a c) (bx b d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

def sumPhase : List Bool → Bool
  | [] => false
  | x :: xs => bx x (sumPhase xs)
def sumPairs : List (Bool × Bool) → Bool
  | [] => false
  | (a,b) :: xs => bx (bx a b) (sumPairs xs)

-- Symmetric difference of arbitrary phase relations, not just pairs/triples.
theorem sum_pair_distrib (xs : List (Bool × Bool)) :
    sumPairs xs =
      bx (sumPhase (xs.map Prod.fst)) (sumPhase (xs.map Prod.snd)) := by
  induction xs with
  | nil => rfl
  | cons p xs ih =>
    rcases p with ⟨a,b⟩
    simp only [sumPairs, List.map_cons, sumPhase, ih]
    exact xor_shuffle a b (sumPhase (xs.map Prod.fst)) (sumPhase (xs.map Prod.snd))

theorem kernel_closed (xs : List (Bool × Bool))
    (h1 : sumPhase (xs.map Prod.fst) = false)
    (h2 : sumPhase (xs.map Prod.snd) = false) : sumPairs xs = false := by
  rw [sum_pair_distrib, h1, h2]
  rfl

end V40
