import Std.Tactic
namespace GVQCC.V28

-- Boolean branch phase of X-basis measurement; qd and qe must be
-- related by h, and the post-measurement omitted coordinate must
-- separately be recoverable. This is the phase obligation only.
theorem representative_phase (m e h : Bool) :
    (m && Bool.xor e h) = Bool.xor (m && e) (m && h) := by
  cases m <;> cases e <;> cases h <;> decide

-- Fuse a nonlinear data update with the exchange of omitted coordinates.
theorem fused_exchange (e h g : Bool) :
    Bool.xor (Bool.xor e h) g = Bool.xor e (Bool.xor h g) := by
  cases e <;> cases h <;> cases g <;> decide

theorem free_exchange (e h : Bool) :
    Bool.xor (Bool.xor e h) h = e := by
  cases e <;> cases h <;> decide

-- Alternating quadratic form elimination: one product replaces all
-- cross terms incident to its two pivots, plus residual A*B.
theorem rank_pair (u v a b : Bool) :
    Bool.xor (Bool.xor (u && v) (u && b)) (v && a) =
    Bool.xor (Bool.xor u a && Bool.xor v b) (a && b) := by
  cases u <;> cases v <;> cases a <;> cases b <;> decide

theorem factor_four (a b c d : Bool) :
    Bool.xor (Bool.xor (a && c) (a && d))
      (Bool.xor (b && c) (b && d)) =
    (Bool.xor a b && Bool.xor c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

-- Real V27 source positions [17228,17235), entry omitted q11,
-- entry q11=q17 xor q20, exit omitted q6 after HMR record 844.
-- a=q17, b=q36, c=q20, d=q31, u=q4, v=q26, w=q29, z=q6.
-- Output projection (q11,q36,q29,q6,phase).
def original (a b c d u v w z m : Bool) :
    Bool × Bool × Bool × Bool × Bool :=
  (Bool.xor (Bool.xor (Bool.xor a c) (a && b)) d,
   b, Bool.xor (Bool.xor w u) v, false,
   m && Bool.xor (Bool.xor z u) v)

-- Physical q11 initially stores logical q36. HMR resets physical q6;
-- three CXs and CCX(q17,q11,q6), then SWAP(q11,q6) reconstruct
-- logical q11 while changing the omitted logical wire to q6.
def candidate (a b c d u v w z m : Bool) :
    Bool × Bool × Bool × Bool × Bool :=
  (Bool.xor (Bool.xor (Bool.xor a c) d) (a && b),
   b, Bool.xor (Bool.xor w u) v, false,
   m && Bool.xor (Bool.xor z u) v)

theorem native17228_projection (a b c d u v w z m : Bool) :
    original a b c d u v w z m = candidate a b c d u v w z m := by
  cases a <;> cases b <;> cases c <;> cases d <;> rfl

theorem coverage_budget :
    44511 + 1174 = 45685 ∧ 321 - 16 = 305 ∧
    22501 + 728 = 23229 ∧ 23229 < 23233 := by decide

end GVQCC.V28
