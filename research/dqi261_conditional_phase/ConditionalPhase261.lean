import Init
import Std
namespace GVQCC.ConditionalPhase261
/-- A measured triple conjunction incurs exactly this three-body phase debt.
    Both outcomes are covered; the expensive correction is needed only at m=1. -/
theorem triple_debt (x y z m : Bool) :
    Bool.xor (((x && y) && z) && m)
      (if m then (x && y && z) else false) = false := by
  cases x <;> cases y <;> cases z <;> cases m <;> decide

theorem triple_repayment (x y z m p : Bool) :
    Bool.xor (Bool.xor p (((x && y) && z) && m))
      (if m then (x && y && z) else false) = p := by
  cases x <;> cases y <;> cases z <;> cases m <;> cases p <;> decide

def active : List Bool → Bool
  | [] => false
  | x :: xs => x || active xs

def pairing : List Bool → List Bool → Bool
  | x :: xs, y :: ys => Bool.xor (x && y) (pairing xs ys)
  | _, _ => false

theorem zero_pairing (m q : List Bool) (h : active m = false) :
    pairing m q = false := by
  induction m generalizing q with
  | nil => rfl
  | cons x xs ih =>
    cases q with
    | nil => rfl
    | cons y ys =>
      cases x with
      | false =>
        have h' : active xs = false := by simpa [active] using h
        simp [pairing, ih ys h']
      | true => simp [active] at h

theorem exact_public_bypass (m q : List Bool) :
    (if active m then pairing m q else false) = pairing m q := by
  cases h : active m with
  | false => simp [zero_pairing m q h]
  | true => simp

theorem bypass_full_oracle {S M : Type} (phase : S → M → Bool)
    (active : M → Bool) (h : ∀ s m, active m = false → phase s m = false)
    (s : S) (m : M) :
    (s,m,if active m then phase s m else false) = (s,m,phase s m) := by
  cases e : active m with
  | false => simp [h s m e]
  | true => simp

theorem phase_sum_zero (a b : Bool) (ha : a = false) (hb : b = false) :
    Bool.xor a b = false := by simp [ha,hb]

/-- Algebraic transport for fraction-free polynomial extended Euclid.
    Multiplication by monomials and leading coefficients is represented
    by ring multiplication, so this lemma is independent of degree gaps. -/
theorem fraction_free_transport {R : Type}
    (add mul : R → R → R)
    (assoc : ∀ x y z, mul (mul x y) z = mul x (mul y z))
    (ld : ∀ x y z, mul x (add y z) = add (mul x y) (mul x z))
    (rd : ∀ x y z, mul (add x y) z = add (mul x z) (mul y z))
    (add_reorder : ∀ a b c d, add (add a b) (add c d) = add (add a c) (add b d))
    (A B f g u v w t k l : R)
    (hf : f = add (mul u A) (mul v B))
    (hg : g = add (mul w A) (mul t B)) :
    add (mul k f) (mul l g) =
      add (mul (add (mul k u) (mul l w)) A)
          (mul (add (mul k v) (mul l t)) B) := by
  rw [hf,hg,ld,ld]
  rw [← assoc, ← assoc, ← assoc, ← assoc]
  rw [add_reorder, ← rd, ← rd]

/-- One cancellation lowers the sum of the active degree bounds. -/
theorem degree_budget (a b a' : Nat) (h : a' < a) :
    a' + b < a + b := by omega

/-- A trace of strictly decreasing nonnegative ranks has at most its
    initial rank plus one entries. This is the fixed-slot budget. -/
def decreases : List Nat → Prop
  | [] => True
  | [_] => True
  | a :: b :: xs => b < a ∧ decreases (b :: xs)

theorem bounded_trace (xs : List Nat) (h : decreases xs) :
    xs.length ≤ xs.headD 0 + 1 := by
  induction xs with
  | nil => simp
  | cons a xs ih =>
    cases xs with
    | nil => simp
    | cons b ys =>
      have hd : b < a ∧ decreases (b :: ys) := h
      have hh := ih hd.2
      simp only [List.length_cons, List.headD_cons] at hh ⊢
      omega

/-- A zero divisor is harmless in the zero-source/zero-target chart;
    the unit inverse branch covers every other admitted source. -/
theorem zero_unit_return {F : Type} (zero one : F)
    (mul : F → F → F) (inv0 : F → F)
    (assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (unit : ∀ a, mul one a = a)
    (zero_r : ∀ a, mul a zero = zero)
    (inv_unit : ∀ a, a ≠ zero → mul (inv0 a) a = one)
    (a x : F) (h : a ≠ zero ∨ x = zero) :
    mul (inv0 a) (mul a x) = x := by
  cases h with
  | inl h => rw [← assoc, inv_unit a h, unit]
  | inr h => rw [h, zero_r, zero_r]

#print axioms degree_budget
#print axioms bounded_trace
#print axioms zero_unit_return
#print axioms triple_debt
#print axioms triple_repayment
#print axioms zero_pairing
#print axioms exact_public_bypass
#print axioms bypass_full_oracle
#print axioms phase_sum_zero
#print axioms fraction_free_transport
end GVQCC.ConditionalPhase261

