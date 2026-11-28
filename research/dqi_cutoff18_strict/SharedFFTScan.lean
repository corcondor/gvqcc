import Mathlib

namespace GVQCC.SharedFFTScan

variable {F : Type} [Field F]

/-- Recursive coefficient bank: the two halves at level n+1 each have 2^n words. -/
def Bank (F : Type) : Nat → Type
  | 0 => F
  | n+1 => Bank F n × Bank F n

def addV : (n : Nat) → Bank F n → Bank F n → Bank F n
  | 0, a, b => a+b
  | n+1, a, b => (addV n a.1 b.1, addV n a.2 b.2)

def scaleV : (n : Nat) → F → Bank F n → Bank F n
  | 0, c, a => c*a
  | n+1, c, a => (scaleV n c a.1, scaleV n c a.2)

def zeroV : (n : Nat) → Bank F n
  | 0 => 0
  | n+1 => (zeroV n, zeroV n)

theorem bank_add_assoc (n : Nat) (a b c : Bank F n) :
    addV n (addV n a b) c = addV n a (addV n b c) := by
  induction n with
  | zero => exact add_assoc a b c
  | succ n ih => exact Prod.ext (ih a.1 b.1 c.1) (ih a.2 b.2 c.2)

theorem bank_scale_add (n : Nat) (c d : F) (b : Bank F n) :
    scaleV n (c+d) b = addV n (scaleV n c b) (scaleV n d b) := by
  induction n with
  | zero => exact add_mul c d b
  | succ n ih => exact Prod.ext (ih b.1) (ih b.2)

theorem bank_scale_one (n : Nat) (a : Bank F n) : scaleV n 1 a = a := by
  induction n with
  | zero => exact one_mul a
  | succ n ih => exact Prod.ext (ih a.1) (ih a.2)

theorem bank_scale_zero (n : Nat) (a : Bank F n) : scaleV n 0 a = zeroV n := by
  induction n with
  | zero => exact zero_mul a
  | succ n ih => exact Prod.ext (ih a.1) (ih a.2)

theorem bank_add_zero (n : Nat) (a : Bank F n) : addV n a (zeroV n) = a := by
  induction n with
  | zero => exact add_zero a
  | succ n ih => exact Prod.ext (ih a.1) (ih a.2)

theorem bank_zero_scale (n : Nat) (c : F) : scaleV n c (zeroV n : Bank F n) = zeroV n := by
  induction n with
  | zero => exact mul_zero c
  | succ n ih => exact Prod.ext ih ih

theorem bank_double_zero (h : (2:F)=0) (n : Nat) (a : Bank F n) :
    addV n a a = zeroV n := by
  induction n with
  | zero =>
      change a+a=0
      rw [← two_mul, h, zero_mul]
  | succ n ih => exact Prod.ext (ih a.1) (ih a.2)

def shear (n : Nat) (c : F) (a b : Bank F n) : Bank F n :=
  addV n a (scaleV n c b)

/-- These are the literal three shears c, 1, c+1 in prepare_fft.py. -/
theorem shear_next (n : Nat) (c : F) (a b : Bank F n) :
    addV n (shear n c a b) b = shear n (c+1) a b := by
  unfold shear
  rw [bank_add_assoc, bank_scale_add, bank_scale_one]

theorem shear_cancel (h : (2:F)=0) (n : Nat) (c : F) (a b : Bank F n) :
    shear n c (shear n c a b) b = a := by
  unfold shear
  rw [bank_add_assoc, bank_double_zero h, bank_add_zero]

theorem shear_inactive (n : Nat) (c : F) (a : Bank F n) :
    shear n c a (zeroV n) = a := by
  unfold shear
  rw [bank_zero_scale, bank_add_zero]

/-- The offset-dependent normalized subspace value c at each internal node. -/
def Plan (F : Type) : Nat → Type
  | 0 => Unit
  | n+1 => F × (Plan F n × Plan F n)

/-- Independent subtree evaluation, no mutation shared between siblings. -/
def expected : (n : Nat) → Bank F n → Plan F n → Bank F n
  | 0, a, _ => a
  | n+1, a, p =>
      (expected n (shear n p.1 a.1 a.2) p.2.1,
       expected n (shear n (p.1+1) a.1 a.2) p.2.2)

/-- The in-place depth-first program, with child state returned before moving
    to the other child. Output is (restored coefficient bank, leaf values). -/
def scan : (n : Nat) → Bank F n → Plan F n → Bank F n × Bank F n
  | 0, a, _ => (a,a)
  | n+1, a, p =>
      let l := scan n (shear n p.1 a.1 a.2) p.2.1
      let r := scan n (addV n l.1 a.2) p.2.2
      ((shear n (p.1+1) r.1 a.2,a.2),(l.2,r.2))

/-- Full recursive algorithm equivalence, not merely a one-step identity.
    Every leaf value agrees and the entire coefficient bank is restored. -/
theorem scan_correct (h : (2:F)=0) (n : Nat) (a : Bank F n) (p : Plan F n) :
    scan n a p = (a,expected n a p) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      rcases a with ⟨lo,hi⟩
      rcases p with ⟨c,pl,pr⟩
      simp only [scan, expected, ih, shear_next, shear_cancel h]

theorem scan_restores (h : (2:F)=0) (n : Nat) (a : Bank F n) (p : Plan F n) :
    (scan n a p).1 = a := by rw [scan_correct h]; rfl

theorem scan_inactive (h : (2:F)=0) (n : Nat) (a : Bank F n) (c : F)
    (pl pr : Plan F n) :
    scan (n+1) (a,zeroV n) (c,pl,pr) =
      ((a,zeroV n),(expected n a pl,expected n a pr)) := by
  rw [scan_correct h]
  simp only [expected, shear_inactive]

/-- Independent product-basis semantics along a path. -/
def Point (F : Type) : Nat → Type
  | 0 => Unit
  | n+1 => F × Point F n

def evaluate : (n : Nat) → Bank F n → Point F n → F
  | 0, a, _ => a
  | n+1, a, p => evaluate n a.1 p.2 + p.1*evaluate n a.2 p.2

theorem evaluate_add (n : Nat) (a b : Bank F n) (p : Point F n) :
    evaluate n (addV n a b) p = evaluate n a p + evaluate n b p := by
  induction n with
  | zero => rfl
  | succ n ih =>
      simp only [evaluate, addV, ih]
      ring

theorem evaluate_scale (n : Nat) (c : F) (a : Bank F n) (p : Point F n) :
    evaluate n (scaleV n c a) p = c*evaluate n a p := by
  induction n with
  | zero => rfl
  | succ n ih =>
      simp only [evaluate, scaleV, ih]
      ring

def Path : Nat → Type
  | 0 => Unit
  | n+1 => Bool × Path n

def atPath : (n : Nat) → Bank F n → Path n → F
  | 0, a, _ => a
  | n+1, a, p => if p.1 then atPath n a.2 p.2 else atPath n a.1 p.2

def pointAt : (n : Nat) → Plan F n → Path n → Point F n
  | 0, _, _ => ()
  | n+1, p, i =>
      if i.1 then (p.1+1,pointAt n p.2.2 i.2)
      else (p.1,pointAt n p.2.1 i.2)

/-- The non-mutating recursive evaluator agrees with the product basis
    itself at every path, including all zero-padded high coefficients. -/
theorem expected_evaluate (n : Nat) (a : Bank F n) (p : Plan F n) (i : Path n) :
    atPath n (expected n a p) i = evaluate n a (pointAt n p i) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      rcases i with ⟨b,j⟩
      cases b <;> simp [expected, atPath, pointAt, evaluate, ih, shear, evaluate_add, evaluate_scale]

theorem scan_leaf (h : (2:F)=0) (n : Nat) (a : Bank F n) (p : Plan F n) (i : Path n) :
    atPath n (scan n a p).2 i = evaluate n a (pointAt n p i) := by
  rw [scan_correct h]
  exact expected_evaluate n a p i

#print axioms bank_add_assoc
#print axioms bank_scale_add
#print axioms bank_scale_one
#print axioms bank_scale_zero
#print axioms bank_add_zero
#print axioms bank_zero_scale
#print axioms bank_double_zero
#print axioms shear_next
#print axioms shear_cancel
#print axioms shear_inactive
#print axioms scan_correct
#print axioms scan_restores
#print axioms scan_inactive
#print axioms evaluate_add
#print axioms evaluate_scale
#print axioms expected_evaluate
#print axioms scan_leaf

end GVQCC.SharedFFTScan
