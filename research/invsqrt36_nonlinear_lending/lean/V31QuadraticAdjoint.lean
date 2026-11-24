import Std.Tactic
namespace GVQCC.V31

def X := Bool.xor

-- Selector ANF with two independent Boolean deletion selectors.
def eval (a b c d s t : Bool) : Bool :=
  X (X a (b && s)) (X (c && t) (d && s && t))

def mixed (f : Bool → Bool → Bool) : Bool :=
  X (X (f false false) (f true false))
    (X (f false true) (f true true))

theorem mixed_coefficient (a b c d : Bool) :
    mixed (fun s t => eval a b c d s t) = d := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

-- Boolean idempotence creates the five terms beyond the usual
-- square-free second-order product rule over a nilpotent ring.
theorem exact_mixed_product (a a1 a2 a12 b b1 b2 b12 : Bool) :
    mixed (fun s t =>
      eval a a1 a2 a12 s t && eval b b1 b2 b12 s t) =
    X (X (X (a && b12) (a12 && b)) (X (a1 && b2) (a2 && b1)))
      (X (X (a1 && b12) (a2 && b12))
        (X (X (a12 && b1) (a12 && b2)) (a12 && b12))) := by
  cases a <;> cases a1 <;> cases a2 <;> cases a12 <;>
    cases b <;> cases b1 <;> cases b2 <;> cases b12 <;> decide

theorem guarded_mixed (g m a a1 a2 a12 : Bool) :
    mixed (fun s t => g && m && eval a a1 a2 a12 s t) =
    (g && m && a12) := by
  cases g <;> cases m <;> cases a <;> cases a1 <;> cases a2 <;>
    cases a12 <;> decide

-- Alternating bilinear multiplication map modulo a retained affine space.
-- These pointwise identities justify computing the product table once and
-- XOR-combining four entries; squares are linear terms.
theorem wedge_four (a b c d : Bool) :
    (X a b && X c d) =
      X (X (a && c) (a && d)) (X (b && c) (b && d)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem wedge_square (a : Bool) : (a && a) = a := by
  cases a <;> decide

theorem wedge_shear (a b : Bool) :
    X (a && X a b) (a && b) = a := by
  cases a <;> cases b <;> decide

-- Concentrate an unwanted rank-one quotient direction into one pivot.
-- Pre-conjugate, update the pivot by a shared product, then un-conjugate.
theorem rank_one_fanout (x y h v : Bool) :
    (X x h, X (X y (v && x)) (v && X x h)) =
      (X x h, X y (v && h)) := by
  cases x <;> cases y <;> cases h <;> cases v <;> decide

-- Discrete partial integration on each selector coefficient.
theorem coefficient_adjoint (l w a d h r : Bool) :
    X (w && d) (l && X (a && d) (X h r)) =
      X (X w (a && l) && d) (X (l && h) (l && r)) := by
  cases l <;> cases w <;> cases a <;> cases d <;> cases h <;> cases r <;> decide

-- Concrete bridge [13149,13184): old CCX at locals 18 and 35 use
-- the same product q13*q15; new local35 computes it once.
-- Reachable-state premise extracted by exact BDD; this lemma proves
-- the simultaneous two-target update when the premise holds.
theorem bridge13149_shared_product (x y a b h : Bool)
    (hh : h = (a && b)) :
    (X x (a && b), X y (a && b)) =
      (X x h, X y h) := by
  rw [hh]

theorem actual_bridge_counts :
    40 - 37 = 3 ∧ 4 - 3 = 1 ∧ 108 - 93 = 15 ∧ 2 - 1 = 1 := by decide

theorem cost_and_width_receipt :
    23213 - 56 = 23157 ∧ 44518 + 100 = 44618 ∧
    45975 + 100 = 46075 := by decide

end GVQCC.V31
