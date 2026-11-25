import Std.Tactic
namespace GVQCC.V39
def x (a b : Bool) : Bool := Bool.xor a b

theorem affine_factor_shift (a b l : Bool) :
    x l (a && b) = x (x l a) (a && x b a) := by
  cases a <;> cases b <;> cases l <;> decide

theorem dirty_cubic (a b c r : Bool) :
    x ((x r (a && b)) && c) (r && c) = (a && b && c) := by
  cases a <;> cases b <;> cases c <;> cases r <;> decide

theorem rank_one_fanout (a b u v : Bool) :
    let u' := x u (a && b)
    let v' := x (x v u) u'
    (u',v') = (x u (a && b),x v (a && b)) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide

theorem guarded_phase_adjoint (g a b t w : Bool) :
    x (g && x t (g && a && b) && w) (g && t && w) =
      (g && a && b && w) := by
  cases g <;> cases a <;> cases b <;> cases t <;> cases w <;> decide

theorem phase_adjoint_distinct_guard (g h a b t w : Bool) :
    x (h && x t (g && a && b) && w) (h && t && w) =
      (g && h && a && b && w) := by
  cases g <;> cases h <;> cases a <;> cases b <;> cases t <;> cases w <;> decide

theorem covector_transport (a d b : Bool) :
    (x (x a d) d && b) = (a && b) := by
  cases a <;> cases d <;> cases b <;> decide

theorem measured_factor (m a b l : Bool) :
    (m && x l (a && b)) = x (m && l) (m && a && b) := by
  cases m <;> cases a <;> cases b <;> cases l <;> decide

def parity : List Bool → Bool
  | [] => false
  | a :: as => x a (parity as)

theorem parity_double (as : List Bool) : x (parity as) (parity as) = false := by
  cases h : parity as <;> decide

theorem clean_presample (m c : Bool) :
    x (m && false) (m && c) = (m && c) := by
  cases m <;> cases c <;> decide

theorem reported_arithmetic :
    2809 - 90 - 99 = 2620 ∧
    26159 - 112 = 26047 ∧
    3149 - 39 = 3110 ∧
    23095 + 136 = 23231 := by decide
end GVQCC.V39
