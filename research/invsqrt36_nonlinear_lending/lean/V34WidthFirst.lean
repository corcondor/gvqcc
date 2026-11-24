import Std.Tactic
namespace GVQCC.V34

-- A zero-wire HMR with outcome m has no input-dependent sign.
-- Move the same independent outcome to the original erasure's phase term.
theorem prefetched_sign (m q p : Bool) :
    Bool.xor p (m && q) =
      Bool.xor (Bool.xor p (m && false)) (m && q) := by
  cases m <;> cases q <;> cases p <;> decide

-- Complemented carrier packing on a partial reachable domain.
theorem mux_restore (a b s : Bool)
    (h : (a && b) = false)
    (hs : a = (Bool.xor a b && s)) :
    (Bool.xor a b && s) = a ∧
    Bool.xor (Bool.xor a b) (Bool.xor a b && s) = b := by
  cases a <;> cases b <;> cases s <;> (first | decide | contradiction)

theorem mux_phase (a b s m : Bool)
    (hs : a = (Bool.xor a b && s)) :
    Bool.xor (m && a) (m && Bool.xor a b && s) = false := by
  cases a <;> cases b <;> cases s <;> cases m <;> (first | decide | contradiction)

-- The actual V33 window [12373,12706): q15, complemented q29, selector q0.
-- Reachability hypotheses checked separately using exact BDD.
theorem actual_mux (q15 q29 q0 m : Bool)
    (h : (q15 && !q29) = false)
    (hs : q15 = (Bool.xor q15 (!q29) && q0)) :
    Bool.xor (m && q15) (m && Bool.xor q15 (!q29) && q0) = false ∧
    !(Bool.xor (Bool.xor q15 (!q29)) (Bool.xor q15 (!q29) && q0)) = q29 := by
  cases q15 <;> cases q29 <;> cases q0 <;> cases m <;> (first | decide | contradiction)

-- Actual V33 interval [31632,32391): q18 = q8*q29 at both endpoints.
-- Intermediate body never reads/writes q18; the endpoint functions may differ.
theorem parked_phase (q a b m : Bool) (h : q = (a && b)) :
    Bool.xor (m && q) (m && a && b) = false := by
  cases q <;> cases a <;> cases b <;> cases m <;> (first | decide | contradiction)

theorem parked_restore (a b q : Bool) (h : q = (a && b)) :
    Bool.xor false (a && b) = q := by
  cases a <;> cases b <;> cases q <;> (first | decide | contradiction)

-- Polar rank-one factorization, including cancellation of the common edge.
theorem polar_factor (a b c d : Bool) :
    Bool.xor (Bool.xor (a && b) (a && d))
      (Bool.xor (c && b) (c && d)) =
      (Bool.xor a c && Bool.xor b d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

-- Two adjacent measured carry differences and their shared boundary.
theorem carry_adjoint (a b c k l : Bool) :
    Bool.xor (k && Bool.xor a b) (l && Bool.xor b c) =
      Bool.xor (Bool.xor (k && a) (Bool.xor k l && b)) (l && c) := by
  cases a <;> cases b <;> cases c <;> cases k <;> cases l <;> decide

theorem resources :
    5264 - 688 = 4576 ∧ 5264 - 731 = 4533 ∧
    22981 + 15*16 = 23221 ∧ 22981 + 23*16 = 23349 ∧
    12706 - 12373 = 333 ∧ 32391 - 31632 = 759 := by decide
end GVQCC.V34
