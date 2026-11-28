import Std

namespace GVQCC.JointFieldPhase

def x (a b : Bool) := Bool.xor a b

theorem guarded_cubic_transport (g a b c d : Bool) :
    x (g && a && b && c) (g && a && b && d) =
      (g && a && b && x c d) := by
  cases g <;> cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem moved_guarded_cubic (g g' a a' b b' c c' d : Bool)
    (hg : g = g') (ha : a = a') (hb : b = b') (hc : c = c') :
    x (g && a && b && c) (g' && a' && b' && d) =
      (g' && a' && b' && x c' d) := by
  rw [hg, ha, hb, hc]
  apply guarded_cubic_transport

theorem shear_phase (g c d : Bool) :
    x (x d (g && c)) (g && c) = d := by
  cases g <;> cases c <;> cases d <;> decide

theorem measured_delta (s v d : Bool) :
    x (s && v) (s && x v d) = (s && d) := by
  cases s <;> cases v <;> cases d <;> decide

theorem joint_chart {S T U : Type} (F : S → T) (H : T → U)
    (G : T → T) (Gi : T → T)
    (h : ∀ t, Gi (G t) = t) (P : S → Bool) (Q : T → Bool)
    (s : S) (phi : Bool) :
    (H (Gi (G (F s))), x (x phi (P s)) (Q (Gi (G (F s))))) =
    (H (F s), x (x phi (P s)) (Q (F s))) := by
  rw [h]

end GVQCC.JointFieldPhase
#print axioms GVQCC.JointFieldPhase.guarded_cubic_transport
#print axioms GVQCC.JointFieldPhase.moved_guarded_cubic
#print axioms GVQCC.JointFieldPhase.shear_phase
#print axioms GVQCC.JointFieldPhase.measured_delta
#print axioms GVQCC.JointFieldPhase.joint_chart

namespace GVQCC.JointFieldPhase

structure Dual (K : Type) where
  constant : K
  tangent : K

def dualMul {K : Type} (add mul : K → K → K) (a b : Dual K) : Dual K :=
  ⟨mul a.constant b.constant,
   add (mul a.constant b.tangent) (mul a.tangent b.constant)⟩

theorem dual_square_tangent_zero {K : Type} (add mul : K → K → K) (zero : K)
    (comm : ∀ a b, mul a b = mul b a) (char2 : ∀ t, add t t = zero) (a : Dual K) :
    (dualMul add mul a a).tangent = zero := by
  change add (mul a.constant a.tangent) (mul a.tangent a.constant) = zero
  rw [comm a.tangent a.constant]
  exact char2 _

def parity (L : List Bool) : Bool :=
  match L with
  | [] => false
  | a :: t => x a (parity t)

theorem guard_parity (g : Bool) (L : List Bool) :
    (g && parity L) = parity (L.map fun a => g && a) := by
  cases g with
  | false => induction L with
    | nil => decide
    | cons a t ih =>
      simp only [List.map_cons, Bool.false_and, parity]
      change false = x false (parity (t.map fun a => false && a))
      rw [← ih]
      simp [x]
  | true =>
    simp

end GVQCC.JointFieldPhase
#print axioms GVQCC.JointFieldPhase.dual_square_tangent_zero
#print axioms GVQCC.JointFieldPhase.guard_parity
