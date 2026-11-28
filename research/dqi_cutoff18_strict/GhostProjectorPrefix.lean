import Mathlib
namespace GVQCC.GhostProjectorPrefix

def bx (a b : Bool) : Bool := Bool.xor a b

def walk : Bool → List (Bool × Bool) → Bool
  | a, [] => a
  | a, (x,d)::xs => walk (bx d (a && x)) xs

theorem step_delta (a b x d : Bool) :
    bx (bx d (a && x)) (bx d (b && x)) = (bx a b && x) := by
  cases a <;> cases b <;> cases x <;> cases d <;> decide

theorem walk_delta (a b : Bool) (xs : List (Bool × Bool)) :
    bx (walk a xs) (walk b xs) = (bx a b && xs.all Prod.fst) := by
  induction xs generalizing a b with
  | nil => cases a <;> cases b <;> decide
  | cons p ps ih =>
    rcases p with ⟨x,d⟩
    change bx (walk (bx d (a && x)) ps) (walk (bx d (b && x)) ps) =
      (bx a b && (x && ps.all Prod.fst))
    rw [ih, step_delta]
    cases a <;> cases b <;> cases x <;> rfl

theorem echo_payload (a b c d v t : Bool) :
    bx (bx t (bx a b && v)) (bx c d && v) =
      bx t (bx (bx a c) (bx b d) && v) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases v <;> cases t <;> decide

theorem odd_flag (r s : Bool) : bx r (r && s) = (r && !s) := by
  cases r <;> cases s <;> decide

section Ring
variable {R : Type*} [CommRing R]

theorem projector_physical (x y : R) (h2 : (2 : R) = 0) (h : y = x) :
    (1+x+y)^2 = 1 := by
  rw [h]
  calc
    _ = (1+2*x)^2 := by ring
    _ = 1 := by simp [h2]

theorem projector_ghost (x y : R) (h2 : (2 : R) = 0) (h : y = x+1) :
    (1+x+y)^2 = 0 := by
  rw [h]
  calc
    _ = (2*(1+x))^2 := by ring
    _ = 0 := by simp [h2]

theorem nilpotent_one (n : R) (h2 : (2 : R) = 0) (hn : n^2 = 0) :
    (1+n)^2 = 1 := by
  calc
    _ = 1+2*n+n^2 := by ring
    _ = 1 := by simp [h2, hn]

theorem projector_preserves (e v : R) (h : e = 1) : e*v = v := by simp [h]
theorem projector_annihilates (e v : R) (h : e = 0) : e*v = 0 := by simp [h]
end Ring

theorem cost_count : 592 - 234 = (358 : Nat) := by decide
end GVQCC.GhostProjectorPrefix

#print axioms GVQCC.GhostProjectorPrefix.step_delta
#print axioms GVQCC.GhostProjectorPrefix.walk_delta
#print axioms GVQCC.GhostProjectorPrefix.echo_payload
#print axioms GVQCC.GhostProjectorPrefix.odd_flag
#print axioms GVQCC.GhostProjectorPrefix.projector_physical
#print axioms GVQCC.GhostProjectorPrefix.projector_ghost
#print axioms GVQCC.GhostProjectorPrefix.nilpotent_one
#print axioms GVQCC.GhostProjectorPrefix.projector_preserves
#print axioms GVQCC.GhostProjectorPrefix.projector_annihilates
#print axioms GVQCC.GhostProjectorPrefix.cost_count
