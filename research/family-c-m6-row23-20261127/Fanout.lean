import Init
namespace GVQCC.MainFanout
def bx (a b : Bool) := Bool.xor a b
-- A hub may be a dirty target; conjugation broadcasts one quadratic update.
theorem dirty_hub (a b h x : Bool) :
    bx (bx x h) (bx h (a && b)) = bx x (a && b) := by
  cases a <;> cases b <;> cases h <;> cases x <;> decide
theorem hub_list (a b h : Bool) (xs : List Bool) :
    (xs.map (fun x => bx x h)).map (fun x => bx x (bx h (a && b))) =
      xs.map (fun x => bx x (a && b)) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.map_cons, dirty_hub, ih]
-- Control complement simplification in the final encoded word chart.
theorem encoded24 (v5 v4 p : Bool) :
    !(bx (bx v5 v4) ((!p) && v4)) = !(bx v5 (p && v4)) := by
  cases v5 <;> cases v4 <;> cases p <;> decide
end GVQCC.MainFanout
#print axioms GVQCC.MainFanout.dirty_hub
#print axioms GVQCC.MainFanout.hub_list
#print axioms GVQCC.MainFanout.encoded24
