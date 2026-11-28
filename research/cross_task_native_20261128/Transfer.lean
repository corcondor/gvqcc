-- Local algebra used by the cross-task affine and HMR-transfer pass.
-- Not a proof of the complete KMB or its decoding correctness.
namespace CrossTaskNative
def bx (a b : Bool) : Bool := Bool.xor a b
def prod (a b : Bool) : Bool := a && b
def cx (g a b : Bool) : Bool := if g then bx a b else b
theorem cx_involution (g a b : Bool) : cx g a (cx g a b) = b := by
  cases g <;> cases a <;> cases b <;> decide
theorem equal_maps_under_guard (f h : S → S) (eq : ∀ x, f x = h x) (g : Bool) (x : S) :
    (if g then f x else x) = (if g then h x else x) := by
  cases g <;> simp [eq]
theorem shared_factor (g a b c : Bool) :
    prod g (prod a (bx b c)) = bx (prod g (prod a b)) (prod g (prod a c)) := by
  cases g <;> cases a <;> cases b <;> cases c <;> decide
theorem measured_adjoint (m a b c : Bool) :
    bx (prod m a) (prod m (bx b c)) = prod m (bx (bx a b) c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide
theorem inactive_ccz (a b c p : Bool) :
    bx p (prod false (prod a (prod b c))) = p := by
  cases a <;> cases b <;> cases c <;> cases p <;> decide
end CrossTaskNative
#print axioms CrossTaskNative.cx_involution
#print axioms CrossTaskNative.equal_maps_under_guard
#print axioms CrossTaskNative.shared_factor
#print axioms CrossTaskNative.measured_adjoint
#print axioms CrossTaskNative.inactive_ccz
