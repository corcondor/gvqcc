import Init
namespace GVQCC.Joint897
def bx (a b : Bool) := Bool.xor a b
def choose (p n d : Bool) : Bool := if p then n else d
def cswap (p n d : Bool) : Bool × Bool := (choose p d n,choose p n d)
def debt (p n d m : Bool) : Bool :=
 bx (m && d) (bx ((m && p) && d) ((m && p) && n))

/-- Transpose a classical masked Z through two quantum controlled swaps.
No assumption on the pole flag or on N,D. The data pair is restored. -/
theorem masked_swap_phase (p n d m phase : Bool) :
    let s := cswap p n d
    (cswap p s.1 s.2,bx phase (m && s.2)) =
      ((n,d),bx phase (debt p n d m)) := by
  cases p <;> cases n <;> cases d <;> cases m <;> cases phase <;> decide

/-- The simpler two-term repayment is only valid under the stated pole invariant. -/
theorem zero_chart_shortcut (p n d m : Bool) (h : p = true → d = false) :
    debt p n d m = bx (m && d) ((m && p) && n) := by
  cases p <;> cases n <;> cases d <;> cases m <;> simp_all [debt,bx,Bool.xor]

def wordPhase (p : Bool) : List (Bool × Bool × Bool) → Bool
 | [] => false
 | (n,d,m)::xs => bx (m && choose p n d) (wordPhase p xs)
def transported (p : Bool) : List (Bool × Bool × Bool) → Bool
 | [] => false
 | (n,d,m)::xs => bx (debt p n d m) (transported p xs)

theorem word_phase (p : Bool) (xs : List (Bool × Bool × Bool)) :
    wordPhase p xs = transported p xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    rcases x with ⟨n,d,m⟩
    have h : (m && choose p n d) = debt p n d m := by
      cases p <;> cases n <;> cases d <;> cases m <;> decide
    simp only [wordPhase,transported,h,ih]

/-- Both phases cancel for all measurement outcomes, not merely sampled ones. -/
theorem repayment (p : Bool) (xs : List (Bool × Bool × Bool)) (s : Bool) :
    bx (bx s (wordPhase p xs)) (transported p xs) = s := by
  rw [← word_phase]
  generalize wordPhase p xs = a
  cases s <;> cases a <;> decide

end GVQCC.Joint897
#print axioms GVQCC.Joint897.masked_swap_phase
#print axioms GVQCC.Joint897.zero_chart_shortcut
#print axioms GVQCC.Joint897.word_phase
#print axioms GVQCC.Joint897.repayment
