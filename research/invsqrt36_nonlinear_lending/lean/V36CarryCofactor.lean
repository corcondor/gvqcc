import Std.Tactic
namespace GVQCC.V36

def x (a b : Bool) : Bool := Bool.xor a b

theorem exchange (a b c : Bool) :
    x (a && b) c = x (x a c && b) ((!b) && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem cofactor (a b c f : Bool) :
    (b = false → c = f) →
    x (a && b) c = x (x a c) ((!b) && x f (x a c)) := by
  cases a <;> cases b <;> cases c <;> cases f <;> decide

theorem shared_dual (a b c : Bool) :
    x (x (a && b) a) (x a c) = x (a && b) c := by
  cases a <;> cases b <;> cases c <;> decide

theorem dirty_hub (r p b t : Bool) :
    x (x r p) p = r ∧
      x t ((!b) && x r p) = x t ((!b) && x p r) := by
  cases r <;> cases p <;> cases b <;> cases t <;> decide

theorem cofactor_factor (a b c l1 l2 l3 : Bool) :
    (b = false → c = x (l1 && l2) l3) →
    x (a && b) c =
      x (x a c) ((!b) && x (x l3 (x a c)) (l1 && l2)) := by
  cases a <;> cases b <;> cases c <;> cases l1 <;> cases l2 <;> cases l3 <;> decide

theorem three_stage_parts (c0 c1 c2 c3 m0 m1 m2 : Bool) :
    x (x (m0 && x c0 c1) (m1 && x c1 c2)) (m2 && x c2 c3) =
      x (x (x (m0 && c0) (x m0 m1 && c1)) (x m1 m2 && c2)) (m2 && c3) := by
  cases c0 <;> cases c1 <;> cases c2 <;> cases c3 <;>
    cases m0 <;> cases m1 <;> cases m2 <;> decide

end GVQCC.V36
