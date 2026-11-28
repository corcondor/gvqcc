import Std
namespace LiveAffineHMR

def bx := Bool.xor

theorem update_from_live (a b t l : Bool) (h : (a && b) = l) :
    bx t (a && b) = bx t l := by rw [h]

theorem phase_from_live (a b c l : Bool) (h : (a && b) = l) :
    ((a && b) && c) = (l && c) := by rw [h]

theorem pair_phase (a b c : Bool) :
    (bx a b && c) = bx (a && c) (b && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem hmr_return (a b t l m : Bool) (h : bx t (a && b) = l) :
    bx (bx (m && t) (m && a && b)) (m && l) = false := by
  cases a <;> cases b <;> cases t <;> cases l <;> cases m <;> simp_all [bx]

theorem hmr_guard_return (a b t l g m : Bool) (h : g = true → bx t (a && b) = l) :
    bx (bx (g && m && t) (g && m && a && b)) (g && m && l) = false := by
  cases a <;> cases b <;> cases t <;> cases l <;> cases g <;> cases m <;> simp_all [bx]

theorem guarded_update (g a t : Bool) :
    bx t (g && a) = (if g then bx t a else t) := by
  cases g <;> cases a <;> cases t <;> decide

theorem guarded_assign (g old val : Bool) :
    bx old (g && bx old val) = (if g then val else old) := by
  cases g <;> cases old <;> cases val <;> decide

theorem swap_delta (a b t : Bool) :
    (bx b (a && bx b t), bx t (a && bx b t)) =
      (if a then (t,b) else (b,t)) := by
  cases a <;> cases b <;> cases t <;> decide

#print axioms update_from_live
#print axioms phase_from_live
#print axioms pair_phase
#print axioms hmr_return
#print axioms hmr_guard_return
#print axioms guarded_update
#print axioms guarded_assign
#print axioms swap_delta
end LiveAffineHMR
