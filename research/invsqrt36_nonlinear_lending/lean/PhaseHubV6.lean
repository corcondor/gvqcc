import Std.Tactic.BVDecide

/-! V6 phase-hub identities. These certify Boolean basis/sign semantics,
not the complete measured quantum oracle. All source index ranges use
zero-based half-open native KMB instructions pinned to 6b592145... . -/
namespace GVQCCV6

def bx := Bool.xor

theorem merge_guard (a b p s : Bool) :
    bx (bx s (a && p)) (b && p) = bx s (bx a b && p) := by
  cases a <;> cases b <;> cases p <;> cases s <;> decide

theorem guarded_conjugation_state (g x a : Bool) :
    bx (bx x (g && a)) (g && a) = x := by
  cases g <;> cases x <;> cases a <;> decide

theorem guarded_conjugation_phase (g x a y s : Bool) :
    bx s (g && (bx x (g && a) && y)) =
    bx (bx s (g && (x && y))) (g && (a && y)) := by
  cases g <;> cases x <;> cases a <;> cases y <;> cases s <;> decide

theorem shared_pair (a b x y : Bool) :
    bx ((a && b) && x) ((a && b) && y) =
      ((a && b) && bx x y) := by
  cases a <;> cases b <;> cases x <;> cases y <;> decide

theorem dirty_echo (a b c d t s : Bool) :
    bx (bx s ((bx t (a && b)) && c && d)) (t && c && d) =
      bx s (a && b && c && d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases t <;> cases s <;> decide

-- Actual source instructions [44933,44945) under classical guard 837:
-- CX 14 10; CZ 10 with each of 0,2,5,11,12,16,18,21,27,34; CX 14 10.
def parity10 (a b c d e f g h i j : Bool) : Bool :=
  bx (bx (bx (bx (bx (bx (bx (bx (bx a b) c) d) e) f) g) h) i) j

def originalPhase44933 (m x y a b c d e f g h i j s : Bool) : Bool :=
  let t := bx x (m && y)
  bx s (parity10 (m && t && a) (m && t && b) (m && t && c)
    (m && t && d) (m && t && e) (m && t && f) (m && t && g)
    (m && t && h) (m && t && i) (m && t && j))

theorem actual44933_phase (m x y a b c d e f g h i j s : Bool) :
    originalPhase44933 m x y a b c d e f g h i j s =
      bx s (m && (bx x y) && parity10 a b c d e f g h i j) := by
  unfold originalPhase44933 parity10 bx
  bv_decide

theorem actual44933_state (m x y : Bool) :
    bx (bx x (m && y)) (m && y) = x :=
  guarded_conjugation_state m x y

-- The two equal diagonal bodies in the emitted V6 36Q chart are
-- controlled by classical bits 806 and 808. Their common sign P can be
-- arbitrary; XOR pooling neither assumes independence nor samples outcomes.
theorem actual806_808 (m806 m808 commonP initialSign : Bool) :
    bx (bx initialSign (m806 && commonP)) (m808 && commonP) =
      bx initialSign (bx m806 m808 && commonP) :=
  merge_guard m806 m808 commonP initialSign

-- Static cost of one representative of the two one-paid diagonal blocks.
theorem pool_cost : (1 + 1 : Nat) - 1 = 1 := by decide

end GVQCCV6
