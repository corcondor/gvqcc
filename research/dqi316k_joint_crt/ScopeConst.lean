namespace ScopeConst
inductive Tri where
  | zero | one | unknown
  deriving DecidableEq

def holds : Tri → Bool → Prop
  | .zero, b => b = false
  | .one, b => b = true
  | .unknown, _ => True

def join : Tri → Tri → Tri
  | .zero, .zero => .zero
  | .one, .one => .one
  | _, _ => .unknown

def band : Tri → Tri → Tri
  | .zero, _ => .zero
  | _, .zero => .zero
  | .one, .one => .one
  | _, _ => .unknown

def bxor : Tri → Tri → Tri
  | .zero, .zero => .zero
  | .one, .one => .zero
  | .zero, .one => .one
  | .one, .zero => .one
  | _, _ => .unknown

theorem join_left (x y : Tri) (b : Bool) :
    holds x b → holds (join x y) b := by
  cases x <;> cases y <;> cases b <;> simp [holds, join]

theorem join_right (x y : Tri) (b : Bool) :
    holds y b → holds (join x y) b := by
  cases x <;> cases y <;> cases b <;> simp [holds, join]

theorem branch_merge (x y : Tri) (a b c : Bool) :
    holds x a → holds y b → holds (join x y) (if c then b else a) := by
  cases c
  · intro h _
    exact join_left x y a h
  · intro _ h
    exact join_right x y b h

theorem band_sound (x y : Tri) (a b : Bool) :
    holds x a → holds y b → holds (band x y) (a && b) := by
  cases x <;> cases y <;> cases a <;> cases b <;> simp [holds, band]

theorem bxor_sound (x y : Tri) (a b : Bool) :
    holds x a → holds y b → holds (bxor x y) (a != b) := by
  cases x <;> cases y <;> cases a <;> cases b <;> simp [holds, bxor]

theorem ccx_zero (b t c : Bool) :
    (t != (c && false && b)) = t := by
  cases b <;> cases t <;> cases c <;> decide

theorem ccx_one (b t c : Bool) :
    (t != (c && true && b)) = (t != (c && b)) := by
  cases b <;> cases t <;> cases c <;> decide

theorem ccz_zero (a b c : Bool) :
    (c && a && b && false) = false := by
  cases a <;> cases b <;> cases c <;> decide

theorem ccz_one (a b c : Bool) :
    (c && a && b && true) = (c && a && b) := by
  cases a <;> cases b <;> cases c <;> decide

theorem guarded_self_invert (b : Bool) : (b != b) = false := by
  cases b <;> decide

theorem guarded_neg_self_invert (b : Bool) : (b != !b) = true := by
  cases b <;> decide

#print axioms join_left
#print axioms join_right
#print axioms branch_merge
#print axioms band_sound
#print axioms bxor_sound
#print axioms ccx_zero
#print axioms ccx_one
#print axioms ccz_zero
#print axioms ccz_one
#print axioms guarded_self_invert
#print axioms guarded_neg_self_invert
end ScopeConst
