import Init

namespace GVQCC.FullRewrite

def bx (a b : Bool) := Bool.xor a b

theorem xassoc (a b c : Bool) : bx (bx a b) c = bx a (bx b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem xcomm (a b : Bool) : bx a b = bx b a := by
  cases a <;> cases b <;> decide
theorem xcancel (a b : Bool) : bx a (bx a b) = b := by
  cases a <;> cases b <;> decide
theorem xconstant (a : Bool) : bx a true = !a := by
  cases a <;> decide

-- Products in a common two-dimensional affine chart.
theorem basis_change_a (a b : Bool) : (a && bx a b) = bx a (a && b) := by
  cases a <;> cases b <;> decide
theorem basis_change_b (a b : Bool) : (b && bx a b) = bx b (a && b) := by
  cases a <;> cases b <;> decide
theorem affine_product (a b ac bc : Bool) :
    (bx a ac && bx b bc) =
      bx (bx (a && b) (a && bc)) (bx (ac && b) (ac && bc)) := by
  cases a <;> cases b <;> cases ac <;> cases bc <;> decide

theorem held_xor (a b t w k : Bool) (h : w = (a && b)) :
    bx t (k && a && b) = bx t (k && w) := by
  subst w
  cases a <;> cases b <;> cases t <;> cases k <;> decide

theorem held_complement (a b t w k : Bool) (h : w = !(a && b)) :
    bx t (k && a && b) = bx (bx t k) (k && w) := by
  subst w
  cases a <;> cases b <;> cases t <;> cases k <;> decide

-- HMR replaces exactly a product-erasing CCX, and a conditional CZ repays
-- the outcome phase.  These are the two components of the local refinement.
theorem uncompute_value (a b t : Bool) (h : t = (a && b)) :
    bx t (a && b) = false := by
  subst t
  cases a <;> cases b <;> decide
theorem uncompute_phase (a b t m : Bool) (h : t = (a && b)) :
    bx (m && t) (m && a && b) = false := by
  subst t
  cases a <;> cases b <;> cases m <;> decide
theorem uncompute_one_value (a b t : Bool) (h : t = !(a && b)) :
    bx t (a && b) = true := by
  subst t
  cases a <;> cases b <;> decide
theorem uncompute_one_phase (a b t m : Bool) (h : t = !(a && b)) :
    bx (bx (m && t) (m && a && b)) m = false := by
  subst t
  cases a <;> cases b <;> cases m <;> decide

theorem conditional_reset (x k : Bool) :
    bx x (k && x) = (if k then false else x) := by
  cases x <;> cases k <;> decide
theorem conditional_assign (x y k : Bool) :
    bx x (k && bx x y) = (if k then y else x) := by
  cases x <;> cases y <;> cases k <;> decide

theorem phase_replace (a b c r k : Bool) (h : r = (a && b && c)) :
    (k && a && b && c) = (k && r) := by
  subst r
  cases a <;> cases b <;> cases c <;> cases k <;> decide
theorem phase_pair (a b c u v k : Bool) (h : (a && b && c) = (u && v)) :
    (k && a && b && c) = (k && u && v) := by
  cases k <;> simp_all

theorem cswap_held (c a b w k : Bool) (h : w = (c && bx a b)) :
    (bx a (k && c && bx a b), bx b (k && c && bx a b)) =
      (bx a (k && w), bx b (k && w)) := by
  subst w
  cases c <;> cases a <;> cases b <;> cases k <;> decide

end GVQCC.FullRewrite

#print axioms GVQCC.FullRewrite.xassoc
#print axioms GVQCC.FullRewrite.xcomm
#print axioms GVQCC.FullRewrite.xcancel
#print axioms GVQCC.FullRewrite.xconstant
#print axioms GVQCC.FullRewrite.basis_change_a
#print axioms GVQCC.FullRewrite.basis_change_b
#print axioms GVQCC.FullRewrite.affine_product
#print axioms GVQCC.FullRewrite.held_xor
#print axioms GVQCC.FullRewrite.held_complement
#print axioms GVQCC.FullRewrite.uncompute_value
#print axioms GVQCC.FullRewrite.uncompute_phase
#print axioms GVQCC.FullRewrite.uncompute_one_value
#print axioms GVQCC.FullRewrite.uncompute_one_phase
#print axioms GVQCC.FullRewrite.conditional_reset
#print axioms GVQCC.FullRewrite.conditional_assign
#print axioms GVQCC.FullRewrite.phase_replace
#print axioms GVQCC.FullRewrite.phase_pair
#print axioms GVQCC.FullRewrite.cswap_held
