import Init
namespace GVQCC.V122
set_option autoImplicit false
def cx (a t : Bool) : Bool := Bool.xor t a
def ccx (a b t : Bool) : Bool := Bool.xor t (a && b)
theorem dirty_fanout (a b u v : Bool) :
    (ccx a b u, ccx a b v) =
      (ccx a b u, cx (ccx a b u) (cx u v)) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide
theorem retained_product (a b u v : Bool) :
    (ccx a b u, ccx a b v) =
      (cx (a && b) u, cx (a && b) v) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide
theorem phase_repayment (a b m p : Bool) :
    Bool.xor (Bool.xor p (m && a && b)) (m && a && b) = p := by
  cases a <;> cases b <;> cases m <;> cases p <;> decide
theorem hmr_dead_target (a b t m p : Bool) :
    (false, Bool.xor p (m && ccx a b t)) =
      (false, Bool.xor (Bool.xor p (m && t)) (m && a && b)) := by
  cases a <;> cases b <;> cases t <;> cases m <;> cases p <;> decide
theorem substitute_live (a b w t : Bool) (h : (a && b) = w) :
    ccx a b t = cx w t := by
  unfold ccx cx
  rw [h]
theorem substitute_live_pair (a b w z t : Bool)
    (h : (a && b) = Bool.xor w z) :
    ccx a b t = cx z (cx w t) := by
  cases a <;> cases b <;> cases w <;> cases z <;> cases t <;> simp_all [ccx, cx, Bool.xor]
theorem complement_product (a b w t : Bool) (h : (a && b) = !w) :
    ccx a b t = cx w (!t) := by
  cases a <;> cases b <;> cases w <;> cases t <;> simp_all [ccx, cx, Bool.xor]
theorem product_transport (a b c : Bool) :
    Bool.xor (a && b) (a && c) = (a && Bool.xor b c) := by
  cases a <;> cases b <;> cases c <;> decide
end GVQCC.V122
#print axioms GVQCC.V122.dirty_fanout
#print axioms GVQCC.V122.retained_product
#print axioms GVQCC.V122.phase_repayment
#print axioms GVQCC.V122.hmr_dead_target
#print axioms GVQCC.V122.substitute_live
#print axioms GVQCC.V122.substitute_live_pair
#print axioms GVQCC.V122.complement_product
#print axioms GVQCC.V122.product_transport
