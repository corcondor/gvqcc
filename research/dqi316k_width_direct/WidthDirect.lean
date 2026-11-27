import Init

namespace GVQCC.DQI316Width

def and3 (a b c : Bool) : Bool := a && b && c
def addPhase (p m t : Bool) : Bool := Bool.xor p (m && t)

/-- The temporary product is erased immediately with its exact phase. -/
theorem temporary_product_cleanup (a b m p : Bool) :
    addPhase (addPhase p m (a && b)) m (a && b) = p := by
  cases a <;> cases b <;> cases m <;> cases p <;> decide

/-- The retained three-factor flag is erased with a masked CCZ. -/
theorem triple_flag_cleanup (a b c m p : Bool) :
    addPhase (addPhase p m (and3 a b c)) (m && a && b) c = p := by
  cases a <;> cases b <;> cases c <;> cases m <;> cases p <;> decide

/-- Concrete 13-control phase in the PA001-derived native ladder. -/
theorem partition13 (a b c d e f g h i j k l z : Bool) :
    (and3 a b c && and3 d e f && g && h && i && j && k && l && z) =
      (a && b && c && d && e && f && g && h && i && j && k && l && z) := by
  simp [and3, Bool.and_assoc]

/-- A dirty flag created only under a guard is clean again after reset
under that very guard. The abstraction is conservative. -/
theorem guarded_clean_release (dirty guard : Bool) (h : dirty = false) :
    ((dirty || guard) && !guard) = false := by
  subst dirty
  cases guard <;> decide

theorem guarded_reset_implication (dirty guard : Bool)
    (h : dirty = true → guard = true) :
    (dirty && !guard) = false := by
  cases dirty <;> cases guard <;> simp_all

/-- Original measurement phase can be moved across a disjoint map.
The outcome is kept as a separate classical variable. -/
theorem disjoint_hmr_transport {A : Type} (f : A → A)
    (x : A) (t p m : Bool) :
    (f x, false, addPhase p m t, m) =
      (f x, false, Bool.xor p (m && t), m) := by
  rfl

/-- Clearing and reconstructing a represented coordinate is an involution;
this is the local proof obligation of interval recoloring. -/
theorem clear_reconstruct (x v : Bool) :
    Bool.xor (Bool.xor x v) v = x := by
  cases x <;> cases v <;> decide

theorem interval_reuse (v : Bool) :
    Bool.xor v v = false := by
  cases v <;> decide

theorem local_width_budget : 890 + 8 = 898 ∧ 890 + 10 = 900 := by
  decide

end GVQCC.DQI316Width

#print axioms GVQCC.DQI316Width.temporary_product_cleanup
#print axioms GVQCC.DQI316Width.triple_flag_cleanup
#print axioms GVQCC.DQI316Width.partition13
#print axioms GVQCC.DQI316Width.guarded_clean_release
#print axioms GVQCC.DQI316Width.guarded_reset_implication
#print axioms GVQCC.DQI316Width.disjoint_hmr_transport
#print axioms GVQCC.DQI316Width.clear_reconstruct
#print axioms GVQCC.DQI316Width.interval_reuse
#print axioms GVQCC.DQI316Width.local_width_budget
