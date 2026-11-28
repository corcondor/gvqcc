import Init
namespace GVQCC.CoefficientFusion

def bx (x y : Bool) := Bool.xor x y
-- Rank-one product after translating one operand's linear form.
theorem bilinear_delta (a b h z : Bool) :
    bx (bx z (a && b)) (h && b) = bx z ((bx a h) && b) := by
  cases a <;> cases b <;> cases h <;> cases z <;> decide

theorem scalar_delta (a b h c : Bool) :
    (bx a (h && c) && b) = bx (a && b) (h && (c && b)) := by
  cases a <;> cases b <;> cases h <;> cases c <;> decide

-- A shift of the polynomial coefficient by h is undone before
-- re-evaluating its zero flag. It is not legitimate to clear the flag sooner.
theorem restore_coeff (q h : Bool) : bx (bx q h) h = q := by
  cases q <;> cases h <;> decide

theorem zero_flag_stale_counterexample :
    (!false) != (!(bx false true)) := by decide

-- HMR product is removed with the translated operand, not the original one.
theorem translated_hmr_phase (q y h m : Bool) :
    bx (m && bx (q && y) (h && y)) (m && ((bx q h) && y)) = false := by
  cases q <;> cases y <;> cases h <;> cases m <;> decide

theorem stale_hmr_counterexample :
    bx (true && ((bx false true) && true)) (true && (false && true)) = true := by decide

-- Exclusive gap selector C F, with B=C2=0:
-- replace scalar t by q*t and route the extra low word.  This is only the
-- formal algebra of the local selector, NOT a proof of the converter law.
theorem cf_selector (B C F C2 : Bool) :
    let o := !C && !F
    let sL := !B && !C2 && !o
    let h := !B && C && F && !C2
    bx sL h = (!B && !C2 && bx C F) := by
  cases B <;> cases C <;> cases F <;> cases C2 <;> decide

-- Correction term can be absorbed into an already masked coefficient bit.
theorem mask_fuse (h l q t z : Bool) :
    bx (bx z ((h && q) && t)) (l && t) =
      bx z ((bx (h && q) l) && t) := by
  cases h <;> cases l <;> cases q <;> cases t <;> cases z <;> decide

-- Linear frame transport / dirty target fanout from MAIN, PR #184.
theorem dirty_hub (a b h x : Bool) :
    bx (bx x h) (bx h (a && b)) = bx x (a && b) := by
  cases a <;> cases b <;> cases h <;> cases x <;> decide

-- Pair coefficient formula in a commutative characteristic-two product.
-- This bit-level expansion proves the underlying XOR/AND identity;
-- tensor certificates provide the independent field-basis instantiation.
theorem quadratic_cross (a b c d : Bool) :
    bx (bx ((bx a b) && (bx c d)) (a && c)) (b && d) =
      bx (a && d) (b && c) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

end GVQCC.CoefficientFusion
#print axioms GVQCC.CoefficientFusion.bilinear_delta
#print axioms GVQCC.CoefficientFusion.scalar_delta
#print axioms GVQCC.CoefficientFusion.restore_coeff
#print axioms GVQCC.CoefficientFusion.zero_flag_stale_counterexample
#print axioms GVQCC.CoefficientFusion.translated_hmr_phase
#print axioms GVQCC.CoefficientFusion.stale_hmr_counterexample
#print axioms GVQCC.CoefficientFusion.cf_selector
#print axioms GVQCC.CoefficientFusion.mask_fuse
#print axioms GVQCC.CoefficientFusion.dirty_hub
#print axioms GVQCC.CoefficientFusion.quadratic_cross
