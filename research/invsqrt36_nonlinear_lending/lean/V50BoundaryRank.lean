import Std.Tactic
namespace GVQCC.V50
def x (a b : Bool) : Bool := Bool.xor a b
theorem quadratic_transport (a b da db : Bool) :
    x ((x a da) && (x b db)) (a && b) =
      x (x (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
theorem abel_transport (m0 m1 f0 f1 : Bool) :
    x (m1 && f1) (m0 && f0) =
      x ((x m1 m0) && f1) (m0 && (x f1 f0)) := by
  cases m0 <;> cases m1 <;> cases f0 <;> cases f1 <;> decide
theorem butterfly_complement_sum (n u v : Int) :
    (n-u)+(n-v) = 2*n-(u+v) := by omega
theorem butterfly_complement_difference (n u v : Int) :
    (n-u)-(n-v) = -(u-v) := by omega
theorem weighted_joint (a b c : Int) :
    a*c+b*c=(a+b)*c := by rw [Int.add_mul]
-- The last exchange contradiction, conditional on independently checked
-- rank/membership hypotheses. Does not formalize physical gate semantics.
theorem last_exchange_obstruction {F : Type} (combine : F → F → F)
    (qU qJ : F → Prop) (t : F)
    (cancel : ∀ r, combine r (combine r t) = t)
    (outside : ∀ r s, qU r → qJ s → combine r s ≠ t) :
    ¬ (∃ r, qU r ∧ qJ (combine r t)) := by
  intro h
  obtain ⟨r, hr, hs⟩ := h
  exact outside r (combine r t) hr hs (cancel r)
theorem resource_check :
    23199 = 23183 + 16 ∧ 2765 + 2 = 2767 ∧ 39517 + 1 = 39518 := by decide
end GVQCC.V50
