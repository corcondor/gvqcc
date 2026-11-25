import Std
namespace V53

def bx (a b : Bool) : Bool := Bool.xor a b

theorem conditional_clean (p q d : Bool) (h : (q && d) = false) :
    (q && bx d p) = (q && p) := by
  cases p <;> cases q <;> cases d <;> simp_all [bx, Bool.xor]

theorem borrow_restore (r p : Bool) : bx (bx r p) p = r := by
  cases r <;> cases p <;> decide

theorem guarded_cx_covector (g a b ca cb : Bool) :
    bx (ca && a) (cb && bx b (g && a)) =
      bx (bx ca (g && cb) && a) (cb && b) := by
  cases g <;> cases a <;> cases b <;> cases ca <;> cases cb <;> decide

theorem guarded_phase_pullback (g a b t : Bool) :
    bx (bx t (g && a) && b) (t && b) = (g && a && b) := by
  cases g <;> cases a <;> cases b <;> cases t <;> decide

theorem quadratic_transport (a b da db : Bool) :
    bx ((bx a da) && (bx b db)) (a && b) =
      bx (bx (a && db) (da && b)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem discrete_abel (a b p q : Bool) :
    bx (bx (a && p) (b && q)) (p && bx a b) =
      b && bx p q := by
  cases a <;> cases b <;> cases p <;> cases q <;> decide

theorem shared_factor (a b c : Bool) :
    bx (a && b) (a && c) = (a && bx b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem history_composition (g h a b : Bool) :
    bx (bx b (g && a)) (h && a) = bx b (bx g h && a) := by
  cases g <;> cases h <;> cases a <;> cases b <;> decide

end V53
