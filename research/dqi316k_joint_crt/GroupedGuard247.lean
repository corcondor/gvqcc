import Init
import Std

namespace GVQCC.GroupedGuard247

/-- A coefficient update is a read-only operation on two sources followed by
    a write to a target. No assumptions on the field operation are needed
    beyond commutation of two additions to the same target. -/
structure Term where
  dst : Nat
  src : Nat
  frob : Nat
  deriving DecidableEq

def write {A : Type} (s : Nat â A) (i : Nat) (v : A) : Nat â A :=
  fun k => if k = i then v else s k

def value {A : Type} (mul : A â A â A) (pow : A â A)
    (s : Nat â A) (p : Term) : A :=
  mul (s p.src) (pow (s p.frob))

def step {A : Type} (add mul : A â A â A) (pow : A â A)
    (p : Term) (s : Nat â A) : Nat â A :=
  write s p.dst (add (s p.dst) (value mul pow s p))

def Indep (p q : Term) : Prop :=
  p.dst â  q.src â§ p.dst â  q.frob â§
  q.dst â  p.src â§ q.dst â  p.frob

theorem stable_sources {A : Type} (add mul : A â A â A) (pow : A â A)
    (p q : Term) (s : Nat â A)
    (h1 : p.dst â  q.src) (h2 : p.dst â  q.frob) :
    value mul pow (step add mul pow p s) q = value mul pow s q := by
  simp [value, step, write, Ne.symm h1, Ne.symm h2]

theorem commute {A : Type} (add mul : A â A â A) (pow : A â A)
    (ha : â x y z, add (add x y) z = add (add x z) y)
    (p q : Term) (s : Nat â A) (h : Indep p q) :
    step add mul pow q (step add mul pow p s) =
      step add mul pow p (step add mul pow q s) := by
  have hp := stable_sources add mul pow p q s h.1 h.2.1
  have hq := stable_sources add mul pow q p s h.2.2.1 h.2.2.2
  funext k
  unfold step
  simp only [step] at hp hq
  rw [hp, hq]
  by_cases hkp : k = p.dst
  Â· by_cases hkq : k = q.dst
    Â· have he : p.dst = q.dst := hkp.symm.trans hkq
      simp [write, hkp, he, ha]
    Â· have hqp : q.dst â  p.dst := fun e => hkq (hkp.trans e.symm)
      simp [write, hkp, Ne.symm hqp]
  Â· by_cases hkq : k = q.dst
    Â· have hqp : q.dst â  p.dst := fun e => hkp (hkq.trans e)
      simp [write, hkq, hqp]
    Â· simp [write, hkp, hkq]

/-- An update strictly below the current target reads original coefficients
    while targets are visited in descending order. -/
theorem descending_read (p q : Term)
    (hp : p.src < p.dst â§ p.frob < p.dst)
    (h : p.dst â¤ q.dst) :
    q.dst â  p.src â§ q.dst â  p.frob := by omega

/-- Outside-block inputs may be shared among every update in the block. -/
theorem shared_block (p q : Term) (lo : Nat)
    (hp : lo â¤ p.dst) (hq : lo â¤ q.dst)
    (hpl : p.src < lo â§ p.frob < lo)
    (hql : q.src < lo â§ q.frob < lo) :
    Indep p q := by
  unfold Indep
  omega

/-- A deferred low-input term can pass a later-written smaller target.
    The original descending order protects the other two sources. -/
theorem defer_external (p q : Term) (lo : Nat)
    (hq : lo â¤ q.dst)
    (hpl : p.src < lo â§ p.frob < lo)
    (hord : q.dst â¤ p.dst)
    (hr : q.src < q.dst â§ q.frob < q.dst) :
    Indep p q := by
  unfold Indep
  omega

/-- The shared coherent control may be computed once, used twice, then
    uncomputed; equals independently computing the same two products. -/
theorem shared_control (active x y z a b : Bool) :
    let t := active && x
    (Bool.xor a (t && y), Bool.xor b (t && z)) =
    (Bool.xor a (active && x && y), Bool.xor b (active && x && z)) := by
  rfl

theorem mask_cleanup (active x : Bool) :
    Bool.xor (active && x) (active && x) = false := by
  cases active <;> cases x <;> decide

/-- Adjoint of CX on a Boolean phase character. -/
theorem cx_adjoint (x y u v : Bool) :
    Bool.xor (x && u) ((Bool.xor y x) && v) =
      Bool.xor (x && Bool.xor u v) (y && v) := by
  cases x <;> cases y <;> cases u <;> cases v <;> decide

/-- Rank-product phase repayment for HMR of a product target. -/
theorem ccx_adjoint (x y z m : Bool) :
    Bool.xor ((Bool.xor z (x && y)) && m) ((x && y) && m) = (z && m) := by
  cases x <;> cases y <;> cases z <;> cases m <;> decide

/-- Coherent compute-phase-uncompute lifts exact coordinate refinement to
    the entire oracle, not just its classical output. -/
theorem full_oracle_refinement {A B M : Type} (f g : A â B) (u : B â A)
    (phase : B â M â Bool) (h : â a, f a = g a)
    (hinv : â a, u (f a) = a) (a : A) (m : M) :
    (u (g a), m, phase (g a) m) = (a, m, phase (f a) m) := by
  rw [â h a, hinv]

#print axioms stable_sources
#print axioms commute
#print axioms descending_read
#print axioms shared_block
#print axioms defer_external
#print axioms shared_control
#print axioms mask_cleanup
#print axioms cx_adjoint
#print axioms ccx_adjoint
#print axioms full_oracle_refinement
end GVQCC.GroupedGuard247
