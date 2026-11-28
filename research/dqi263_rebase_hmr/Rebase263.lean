import Init
import Std

namespace GVQCC.Rebase263

def sq (x : BitVec 12) : BitVec 12 :=
  (if x.getLsbD 0 then 1 else 0) ^^^
  (if x.getLsbD 1 then 4 else 0) ^^^
  (if x.getLsbD 2 then 16 else 0) ^^^
  (if x.getLsbD 3 then 64 else 0) ^^^
  (if x.getLsbD 4 then 256 else 0) ^^^
  (if x.getLsbD 5 then 1024 else 0) ^^^
  (if x.getLsbD 6 then 83 else 0) ^^^
  (if x.getLsbD 7 then 332 else 0) ^^^
  (if x.getLsbD 8 then 1328 else 0) ^^^
  (if x.getLsbD 9 then 1171 else 0) ^^^
  (if x.getLsbD 10 then 543 else 0) ^^^
  (if x.getLsbD 11 then 2172 else 0)

def tr (x : BitVec 12) : Bool := x.getLsbD 11

private theorem lsb_choice (b : Bool) (c : BitVec 12) :
    (if b then c else 0).getLsbD 11 = (b && c.getLsbD 11) := by
  cases b <;> simp

theorem square_trace (x : BitVec 12) : tr (sq x) = tr x := by
  unfold tr sq
  simp only [BitVec.getLsbD_xor, lsb_choice]
  change (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.and (x.getLsbD 0) false) (Bool.and (x.getLsbD 1) false)) (Bool.and (x.getLsbD 2) false)) (Bool.and (x.getLsbD 3) false)) (Bool.and (x.getLsbD 4) false)) (Bool.and (x.getLsbD 5) false)) (Bool.and (x.getLsbD 6) false)) (Bool.and (x.getLsbD 7) false)) (Bool.and (x.getLsbD 8) false)) (Bool.and (x.getLsbD 9) false)) (Bool.and (x.getLsbD 10) false)) (Bool.and (x.getLsbD 11) true)) = x.getLsbD 11
  simp only [Bool.and_false, Bool.and_true, Bool.xor_false, Bool.false_xor]

theorem quadratic_trace (x : BitVec 12) :
    tr (sq x ^^^ x) = false := by
  change (sq x ^^^ x).getLsbD 11 = false
  rw [BitVec.getLsbD_xor]
  change (tr (sq x) ^^ tr x) = false
  rw [square_trace, Bool.xor_self]

theorem trace_one_rootfree (x k : BitVec 12) (h : tr k = true) :
    sq x ^^^ x ^^^ k ≠ 0 := by
  intro e
  have hh : tr (sq x ^^^ x ^^^ k) = false := by rw [e]; rfl
  change (sq x ^^^ x ^^^ k).getLsbD 11 = false at hh
  rw [BitVec.getLsbD_xor] at hh
  change (tr (sq x ^^^ x) ^^ tr k) = false at hh
  rw [quadratic_trace, h] at hh
  contradiction

/-- Nonzero marker constants for the old and new low-weight padding charts. -/
theorem marker_constants :
    (tr 2048 && tr 2054 && tr 2068 && tr 2066 && tr 2120 && tr 2126 &&
     tr 2072 && tr 2897 && tr 2206 && tr 2218 && tr 2616 && tr 3281) = true := by decide

/-- A controlled swap, conjugated by a fixed invertible basis map, is an
    involution. This handles both the numerator and denominator subspaces. -/
def swapIf (f : Bool) (a b : A) : A × A :=
  if f then (b,a) else (a,b)

theorem swapIf_involutive {A : Type} (f : Bool) (a b : A) :
    swapIf f (swapIf f a b).1 (swapIf f a b).2 = (a,b) := by
  cases f <;> rfl

theorem controlled_exchange {A B : Type} (to : A → B × B)
    (back : B × B → A) (h₁ : ∀ a, back (to a) = a)
    (h₂ : ∀ p, to (back p) = p) (f : Bool) (a : A) :
    back (swapIf f (to (back (swapIf f (to a).1 (to a).2))).1
                   (to (back (swapIf f (to a).1 (to a).2))).2) = a := by
  simp only [h₂, swapIf_involutive, h₁]

/-- Rebase preserves the physical residue: the padded derivative and
    numerator both contain the same nonzero factor. -/
theorem residue_preserved {F : Type} (mul : F → F → F)
    (assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (comm : ∀ a b, mul a b = mul b a)
    (n d e g g' : F) (h : n = mul e d) :
    mul g n = mul e (mul g d) ∧
    mul g' n = mul e (mul g' d) := by
  constructor
  · rw [h, ← assoc, comm g e, assoc]
  · rw [h, ← assoc, comm g' e, assoc]

theorem phase_repay_marker (f next m : Bool) (h : f = next) :
    Bool.xor (m && f) (if m then next else false) = false := by
  subst next
  cases f <;> cases m <;> decide

theorem conditional_rebase_cleanup (f m oldPhase : Bool) :
    Bool.xor (Bool.xor oldPhase (m && f)) (if m then f else false) = oldPhase := by
  cases f <;> cases m <;> cases oldPhase <;> decide

/-- If all root evaluations are correct, a sum of phase bits is unchanged.
    This is a compositional statement, not a proof of the Euclidean gap bound. -/
theorem phase_fold_eq (xs ys : List Bool) (h : xs = ys) :
    xs.foldl Bool.xor false = ys.foldl Bool.xor false := by rw [h]

#print axioms square_trace
#print axioms quadratic_trace
#print axioms trace_one_rootfree
#print axioms marker_constants
#print axioms swapIf_involutive
#print axioms controlled_exchange
#print axioms residue_preserved
#print axioms phase_repay_marker
#print axioms conditional_rebase_cleanup
#print axioms phase_fold_eq
end GVQCC.Rebase263

