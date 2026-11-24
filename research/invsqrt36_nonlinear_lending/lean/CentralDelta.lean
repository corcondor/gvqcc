import Std.Tactic.BVDecide

/-!
Central delta architecture. A latent Boolean h can be represented by a
translation direction v rather than by a dedicated physical qubit.
The HMR law certifies measured disposal of a redundant carrier, conditional
on a separately certified reachable-state polynomial. These are Boolean
branch phase laws, not the full numerical invsqrt specification.
-/
namespace CentralDelta
def bx := Bool.xor

def project (s v : Nat → Bool) (p q : Nat) : Bool :=
  bx (s q) (v q && s p)

def translate (s v : Nat → Bool) (h : Bool) (q : Nat) : Bool :=
  bx (s q) (v q && h)

theorem projection_bit (x xp v h : Bool) :
    bx (bx x (v && h)) (v && bx xp h) = bx x (v && xp) := by
  cases x <;> cases xp <;> cases v <;> cases h <;> decide

theorem quotient_invariant (s v : Nat → Bool) (p q : Nat) (h : Bool)
    (hp : v p = true) :
    project (translate s v h) v p q = project s v p q := by
  unfold project translate
  rw [hp]
  exact projection_bit (s q) (s p) (v q) h

theorem invariant_control (x h v : Bool) (hv : v = false) :
    bx x (v && h) = x := by
  subst v
  cases x <;> cases h <;> decide

theorem update_projection (x xp v tq tp product : Bool) :
    bx (bx x (tq && product)) (v && bx xp (tp && product)) =
      bx (bx x (v && xp)) ((bx tq (v && tp)) && product) := by
  cases x <;> cases xp <;> cases v <;> cases tq <;> cases tp <;>
    cases product <;> decide

theorem shared_and_translation (a b h : Bool) :
    (bx a (false && h) && bx b (false && h)) = (a && b) := by
  cases a <;> cases b <;> cases h <;> decide

theorem decode_projection (x h v : Bool) :
    bx (bx x (v && h)) (v && h) = x := by
  cases x <;> cases h <;> cases v <;> decide

def parity : List Bool → Bool
  | [] => false
  | a :: xs => bx a (parity xs)

theorem and_xor (m a b : Bool) :
    (m && bx a b) = bx (m && a) (m && b) := by
  cases m <;> cases a <;> cases b <;> decide

theorem parity_conditioned (m : Bool) (xs : List Bool) :
    parity (xs.map (fun a => m && a)) = (m && parity xs) := by
  induction xs with
  | nil => cases m <;> rfl
  | cons a xs ih =>
    simp only [List.map_cons, parity, ih]
    rw [and_xor]

theorem measured_clear (incoming m value : Bool) (terms : List Bool)
    (h : value = parity terms) :
    bx (bx incoming (m && value)) (parity (terms.map (fun a => m && a))) =
      incoming := by
  rw [parity_conditioned, ← h]
  cases incoming <;> cases m <;> cases value <;> decide

-- Source cuts 38809 and 38860 from the exact endpoint certificate.
-- The polynomials use different controls; there is no stability assumption.
def entry38809 (q5 q9 q13 q14 q24 q26 q27 : Bool) :=
  parity [q14, q5 && q14, q9 && q14, q13 && q14,
    q14 && q24, q14 && q26, q14 && q27]
def exit38860 (q14 q34 : Bool) := parity [q14, q14 && q34]

theorem entry38809_factored (q5 q9 q13 q14 q24 q26 q27 : Bool) :
    entry38809 q5 q9 q13 q14 q24 q26 q27 =
      (q14 && Bool.not (parity [q5,q9,q13,q24,q26,q27])) := by
  cases q5 <;> cases q9 <;> cases q13 <;> cases q14 <;>
    cases q24 <;> cases q26 <;> cases q27 <;> decide

theorem exit38860_factored (q14 q34 : Bool) :
    exit38860 q14 q34 = (q14 && Bool.not q34) := by
  cases q14 <;> cases q34 <;> decide

theorem entry38809_hmr_phase (q5 q9 q13 q14 q24 q26 q27 phase m value : Bool)
    (h : value = entry38809 q5 q9 q13 q14 q24 q26 q27) :
    bx (bx phase (m && value))
      (parity ([q14, q5 && q14, q9 && q14, q13 && q14,
        q14 && q24, q14 && q26, q14 && q27].map (fun a => m && a))) = phase := by
  exact measured_clear phase m value _ h

end CentralDelta
