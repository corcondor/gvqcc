/-
Independent Lean 4.35 proof kernel for nonlinear coordinate and whole-tail
relational search in GVQCC. No sorry, axiom, or native_decide.
-/
import Init

namespace GVQCC

abbrev Bits (n : Nat) := Fin n → Bool

def xorBits {n : Nat} (s d : Bits n) : Bits n :=
  fun i => Bool.xor (s i) (d i)

def shear {n : Nat} (a b t : Fin n) (s : Bits n) : Bits n :=
  fun i => if i = t then Bool.xor (s i) (Bool.and (s a) (s b)) else s i

private theorem xor_twice (x y : Bool) : Bool.xor (Bool.xor x y) y = x := by
  cases x <;> cases y <;> rfl

/-- Nonlinear triangular coordinate change is an involution, on ALL states. -/
theorem shear_involution {n : Nat} (a b t : Fin n) (s : Bits n)
    (ha : a ≠ t) (hb : b ≠ t) :
    shear a b t (shear a b t s) = s := by
  funext i
  by_cases hi : i = t
  · subst i
    calc
      shear a b t (shear a b t s) t =
        Bool.xor (Bool.xor (s t) (Bool.and (s a) (s b)))
          (Bool.and (s a) (s b)) := by simp [shear, ha, hb]
      _ = s t := xor_twice (s t) (Bool.and (s a) (s b))
  · simp [shear, hi]

/-- Exact polarisation: cross-term da*db cannot be omitted. -/
theorem product_delta (a b da db : Bool) :
    Bool.xor (Bool.and (Bool.xor a da) (Bool.xor b db)) (Bool.and a b) =
      Bool.xor (Bool.xor (Bool.and a db) (Bool.and da b))
        (Bool.and da db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> rfl

def ccxDiff {n : Nat} (a b t : Fin n) (s d : Bits n) : Bits n :=
  fun i => if i = t then
    Bool.xor (d i)
      (Bool.xor (Bool.xor (Bool.and (s a) (d b))
        (Bool.and (d a) (s b))) (Bool.and (d a) (d b)))
    else d i

def ccx {n : Nat} (a b t : Fin n) (s : Bits n) : Bits n :=
  fun i => if i = t then Bool.xor (s i) (Bool.and (s a) (s b)) else s i

/-- Exact differential over a CCX on every incoming state and perturbation. -/
theorem ccx_difference {n : Nat} (a b t : Fin n) (s d : Bits n) :
    ccx a b t (xorBits s d) =
      xorBits (ccx a b t s) (ccxDiff a b t s d) := by
  funext i
  by_cases h : i = t
  · simp only [ccx, ccxDiff, xorBits, if_pos h]
    cases (s i) <;> cases (d i) <;> cases (s a) <;>
      cases (s b) <;> cases (d a) <;> cases (d b) <;> decide
  · simp [ccx, ccxDiff, xorBits, h]

/-- Classical branch representation of the relative phase bit. -/
structure Trace (n : Nat) where
  bits : Bits n
  phase : Bool

def liftShear {n : Nat} (a b t : Fin n) (u : Trace n) : Trace n :=
  { bits := shear a b t u.bits, phase := u.phase }

theorem liftShear_involution {n : Nat} (a b t : Fin n) (u : Trace n)
    (ha : a ≠ t) (hb : b ≠ t) :
    liftShear a b t (liftShear a b t u) = u := by
  cases u with
  | mk bits phase =>
    simp [liftShear, shear_involution a b t bits ha hb]

/-- HMR branch phase (-1)^(m*old_bit), conditional on its unique event. -/
def hmr {n : Nat} (t : Fin n) (m : Bool) (u : Trace n) : Trace n :=
  { bits := fun i => if i = t then false else u.bits i,
    phase := Bool.xor u.phase (Bool.and m (u.bits t)) }

def czWhen {n : Nat} (a b : Fin n) (m : Bool) (u : Trace n) : Trace n :=
  { bits := u.bits,
    phase := Bool.xor u.phase (Bool.and m (Bool.and (u.bits a) (u.bits b))) }

/-- FROZEN end-to-end semantic specification: every reached state and transcript. -/
def CorrectOn {n k : Nat} (reachable : Bits n → Prop)
    (original candidate : (Fin k → Bool) → Trace n → Trace n) : Prop :=
  ∀ (s : Bits n) (m : Fin k → Bool) (p : Bool), reachable s →
    original m ⟨s,p⟩ = candidate m ⟨s,p⟩

/-- Soundness rule for a synthesized, possibly completely different macro-network Q.
The original interior wires need NOT be preserved. -/
theorem conjugation_sound {n : Nat} (a b t : Fin n)
    (ha : a ≠ t) (hb : b ≠ t)
    (reachable : Bits n → Prop)
    (P Q : Trace n → Trace n)
    (h : ∀ (u : Trace n), reachable u.bits →
      Q (liftShear a b t u) = liftShear a b t (P u)) :
    ∀ (u : Trace n), reachable u.bits →
      liftShear a b t (Q (liftShear a b t u)) = P u := by
  intro u hu
  rw [h u hu, liftShear_involution a b t (P u) ha hb]

inductive Gate (n : Nat) where
  | x (t : Fin n)
  | cx (c t : Fin n)
  | ccx (a b t : Fin n)

def costCCX {n : Nat} : List (Gate n) → Nat
  | [] => 0
  | (.ccx _ _ _) :: gs => 1 + costCCX gs
  | _ :: gs => costCCX gs

def Admissible {n k : Nat} (reachable : Bits n → Prop)
    (original candidate : (Fin k → Bool) → Trace n → Trace n)
    (ops : List (Gate n)) (budget : Nat) : Prop :=
  CorrectOn reachable original candidate ∧ costCCX ops ≤ budget

end GVQCC
