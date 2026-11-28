import Init
import Std
namespace GVQCC.CentralSchedule
/-- Call-by-need sharing: if the source is retained, both uses see the same value. -/
theorem let_share {A B C D : Type} (f : A â B) (g : B â C) (h : B â D) (x : A) :
    (let p := f x; (g p, h p)) = (g (f x), h (f x)) := rfl
/-- A lexical computation can be kept live across a consumer of other state,
then erased with the same witness. -/
theorem retained_flag {A B : Type} (p : A â Bool) (use : A â Bool â B â B) (a : A) (x : B) :
    (let f := p a; (use a f x, Bool.xor f (p a))) = (use a (p a) x, false) := by
  cases p a <;> rfl
/-- Dirty-target parity addition is its own inverse. -/
theorem cx_inverse (x y : Bool) : Bool.xor (Bool.xor y x) x = y := by
  cases x <;> cases y <;> decide
theorem controlled_swap_involution (f x y : Bool) :
    (let p := if f then (y,x) else (x,y);
     if f then (p.2,p.1) else p) = (x,y) := by
  cases f <;> rfl
/-- A shared affine context does not alter a nonlinear term's transported output. -/
theorem target_frame_transport (x y a b : Bool) :
    Bool.xor (Bool.xor y x) (Bool.xor x (a && b)) = Bool.xor y (a && b) := by
  cases x <;> cases y <;> cases a <;> cases b <;> decide
/-- HMR debt uses the same bound predicate, even if the physical frame is restored. -/
theorem retained_hmr_debt (p m phase : Bool) :
    Bool.xor (Bool.xor phase (p && m)) (p && m) = phase := by
  cases p <;> cases m <;> cases phase <;> decide
/-- Sum of two phase contributions in either order. -/
theorem phase_schedule (p a b : Bool) :
    Bool.xor (Bool.xor p a) b = Bool.xor (Bool.xor p b) a := by
  cases p <;> cases a <;> cases b <;> decide
#print axioms let_share
#print axioms retained_flag
#print axioms cx_inverse
#print axioms controlled_swap_involution
#print axioms target_frame_transport
#print axioms retained_hmr_debt
#print axioms phase_schedule
end GVQCC.CentralSchedule

