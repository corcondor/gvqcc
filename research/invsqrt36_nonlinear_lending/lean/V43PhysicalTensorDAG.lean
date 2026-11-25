import Std.Tactic
namespace GVQCC.V43
def x (a b : Bool) := Bool.xor a b

theorem shared_factor (a b l : Bool) :
    x l (a && b) = x (x l a) (a && x a b) := by
  cases a <;> cases b <;> cases l <;> decide

theorem crossstage_data (r d c : Bool) :
    let q := x (x r d) c
    (x c q, x (x d (q && d)) q, x q (x c q)) =
      (x d r, x d ((!d) && x c r), c) := by
  cases r <;> cases d <;> cases c <;> decide

theorem crossstage_phase (r d c md mc : Bool) :
    x (md && d) (mc && c) =
      x (x (mc && x c r) (mc && r)) (md && d) := by
  cases r <;> cases d <;> cases c <;> cases md <;> cases mc <;> decide

theorem shared_cz (m l a b : Bool) :
    (m && x l (a && b)) = x (m && l) (m && a && b) := by
  cases m <;> cases l <;> cases a <;> cases b <;> decide

theorem transported_factor (q l : Bool) :
    (l && x l q) = (l && !q) := by
  cases l <;> cases q <;> decide

theorem clean_coin (m : Bool) : (m && false) = false := by
  cases m <;> decide

def widthOK (used : List Nat) : Bool :=
  used.all (fun n => decide (n ≤ 36))

theorem width_append (a b : List Nat)
    (ha : widthOK a = true) (hb : widthOK b = true) :
    widthOK (a ++ b) = true := by
  simp [widthOK, List.all_append] at *
  exact ⟨ha, hb⟩

theorem resource_arithmetic :
    2736 - 2665 = 71 ∧ 2620 - 2557 = 63 ∧
    3415 - 3356 = 59 ∧ 3149 - 3099 = 50 ∧
    23223 - 23095 = 128 ∧ 8644 - 6322 = 2322 := by decide

end GVQCC.V43
