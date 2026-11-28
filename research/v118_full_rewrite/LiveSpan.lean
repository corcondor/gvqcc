import Init
namespace GVQCC.LiveSpan
def bx (a b : Bool) := Bool.xor a b
def par : List Bool → Bool
  | [] => false
  | a::as => bx a (par as)
def writes (t k : Bool) : List Bool → Bool
  | [] => t
  | a::as => writes (bx t (k && a)) k as
theorem swapxor (a b c : Bool) : bx (bx a b) c = bx a (bx b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem distribute (k a b : Bool) : (k && bx a b) = bx (k && a) (k && b) := by
  cases k <;> cases a <;> cases b <;> decide
theorem writes_correct (t k : Bool) (xs : List Bool) :
    writes t k xs = bx t (k && par xs) := by
  induction xs generalizing t with
  | nil => cases t <;> cases k <;> rfl
  | cons a as ih => simp only [writes, par, ih, swapxor, distribute]
theorem paid_to_span (a b t k : Bool) (xs : List Bool)
    (h : (a && b) = par xs) :
    bx t (k && a && b) = writes t k xs := by
  rw [writes_correct, ← h]
  cases a <;> cases b <;> cases t <;> cases k <;> decide
theorem phase_to_span (a b c k : Bool) (xs : List Bool)
    (h : (a && b && c) = par xs) :
    (k && a && b && c) = writes false k xs := by
  rw [writes_correct, ← h]
  cases a <;> cases b <;> cases c <;> cases k <;> decide
-- Rebase elimination substitutes a fresh atom by the exact original function.
-- The equality is valid for all valuations, irrespective of dependencies
-- among the atom functions; enlarging the allowed valuations is conservative.
theorem parity_rebase (a b c : Bool) :
    bx (bx a b) (bx b c) = bx a c := by
  cases a <;> cases b <;> cases c <;> decide
theorem hmr_constant_plus_product (m a b c : Bool) :
    bx (m && bx c (a && b)) (bx (m && c) (m && a && b)) = false := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide
theorem hmr_retained (m a b t : Bool) (h : t = (a && b)) :
    bx (m && t) (m && a && b) = false := by
  subst t
  cases m <;> cases a <;> cases b <;> decide
-- The phase of a retained product must be repaid on an equal *current*
-- expression, not on stale physical wire labels.
theorem stale_counterexample :
    bx (true && (true && true)) (true && false && true) = true := by decide
end GVQCC.LiveSpan
#print axioms GVQCC.LiveSpan.writes_correct
#print axioms GVQCC.LiveSpan.paid_to_span
#print axioms GVQCC.LiveSpan.phase_to_span
#print axioms GVQCC.LiveSpan.parity_rebase
#print axioms GVQCC.LiveSpan.hmr_constant_plus_product
#print axioms GVQCC.LiveSpan.hmr_retained
#print axioms GVQCC.LiveSpan.stale_counterexample
