namespace GVQCC.PolyFrame

inductive Expr where
  | constant (b : Bool)
  | coord (i : Nat)
  | add (a b : Expr)
  | mul (a b : Expr)

def eval (rho : Nat → Bool) : Expr → Bool
  | .constant b => b
  | .coord i => rho i
  | .add a b => Bool.xor (eval rho a) (eval rho b)
  | .mul a b => eval rho a && eval rho b

def setVal (rho : Nat → Bool) (i : Nat) (b : Bool) : Nat → Bool :=
  fun j => if j = i then b else rho j

def subst (i : Nat) (r : Expr) : Expr → Expr
  | .constant b => .constant b
  | .coord j => if j = i then r else .coord j
  | .add a b => .add (subst i r a) (subst i r b)
  | .mul a b => .mul (subst i r a) (subst i r b)

theorem eval_subst (rho : Nat → Bool) (i : Nat) (r e : Expr) :
    eval rho (subst i r e) = eval (setVal rho i (eval rho r)) e := by
  induction e with
  | constant b => rfl
  | coord j => by_cases h : j = i <;> simp [subst, eval, setVal, h]
  | add a b ha hb => simp [subst, eval, ha, hb]
  | mul a b ha hb => simp [subst, eval, ha, hb]

theorem xor_twice (a b : Bool) :
    Bool.xor (Bool.xor a b) b = a := by
  cases a <;> cases b <;> decide

theorem zero_copy (a : Bool) : Bool.xor a a = false := by
  cases a <;> decide

/-- A coordinate update by a known bit transports every virtual Boolean
expression, not only affine or quadratic expressions. The concrete compiler
must separately establish the value of delta at the cut. -/
theorem transport_eval (rho : Nat → Bool) (i : Nat) (delta : Bool) (e : Expr) :
    eval (setVal rho i (Bool.xor (rho i) delta))
      (subst i (.add (.coord i) (.constant delta)) e) = eval rho e := by
  rw [eval_subst]
  have h : setVal (setVal rho i (Bool.xor (rho i) delta)) i
      (eval (setVal rho i (Bool.xor (rho i) delta))
        (.add (.coord i) (.constant delta))) = rho := by
    funext j
    by_cases hj : j = i
    · subst j
      simp [setVal, eval]
    · simp [setVal, hj]
  rw [h]

/-- Exchange a physical pivot with a virtual coordinate v = x XOR rest. -/
theorem pivot_inverse (x rest : Bool) :
    Bool.xor (Bool.xor x rest) rest = x := xor_twice x rest

theorem product_transport (a b c : Bool) :
    ((Bool.xor a b) && c) = Bool.xor (a && c) (b && c) := by
  cases a <;> cases b <;> cases c <;> decide

/-- No clean auxiliary is needed for the three-control toggle: the borrowed
line w, even when nonzero, is returned unchanged. -/
theorem dirty_three_control (a b c w t : Bool) :
    let w1 := Bool.xor w (a && b)
    let t1 := Bool.xor t (w1 && c)
    let w2 := Bool.xor w1 (a && b)
    let t2 := Bool.xor t1 (w2 && c)
    (w2,t2) = (w,Bool.xor t ((a && b) && c)) := by
  cases a <;> cases b <;> cases c <;> cases w <;> cases t <;> decide

/-- The phase witness must equal the old measured value, independently of
the correction circuit. Keeping the original HMR and substituting an
equal witness preserves the Boolean phase exponent. -/
theorem hmr_witness (p m x witness : Bool) (h : x = witness) :
    Bool.xor p (m && x) = Bool.xor p (m && witness) := by
  rw [h]

theorem hmr_repay (p m x : Bool) :
    Bool.xor (Bool.xor p (m && x)) (m && x) = p :=
  xor_twice p (m && x)

theorem two_phase_commute (p m n x y : Bool) :
    Bool.xor (Bool.xor p (m && x)) (n && y) =
    Bool.xor (Bool.xor p (n && y)) (m && x) := by
  cases p <;> cases m <;> cases n <;> cases x <;> cases y <;> decide

end GVQCC.PolyFrame

#print axioms GVQCC.PolyFrame.eval_subst
#print axioms GVQCC.PolyFrame.xor_twice
#print axioms GVQCC.PolyFrame.zero_copy
#print axioms GVQCC.PolyFrame.transport_eval
#print axioms GVQCC.PolyFrame.pivot_inverse
#print axioms GVQCC.PolyFrame.product_transport
#print axioms GVQCC.PolyFrame.dirty_three_control
#print axioms GVQCC.PolyFrame.hmr_witness
#print axioms GVQCC.PolyFrame.hmr_repay
#print axioms GVQCC.PolyFrame.two_phase_commute
