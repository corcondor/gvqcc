import Mathlib

namespace GVQCC.NoCopy
variable {F : Type*} [Field F]

@[ext] structure Frame (F : Type*) where
  n : F
  d : F
  l : F

def step (q h t : F) (x : Frame F) : Frame F :=
  ⟨q*x.d, x.n+h*x.d, q*(x.l+t*x.d^2)⟩

def undo (qi h t : F) (x : Frame F) : Frame F :=
  let d := qi*x.n
  ⟨x.d-h*d,d,qi*x.l-t*d^2⟩

def rescale (r : F) (x : Frame F) : Frame F :=
  ⟨r*x.n,r*x.d,r^2*x.l⟩

theorem step_inverse (q qi h t : F) (hq : qi*q=1) (x : Frame F) :
    undo qi h t (step q h t x) = x := by
  have hm (z : F) : qi*(q*z)=z := by rw [← mul_assoc,hq,one_mul]
  rcases x with ⟨n,d,l⟩
  simp [step,undo,hm]

theorem step_homogeneous (q h t r : F) (x : Frame F) :
    step q h t (rescale r x) = rescale r (step q h t x) := by
  apply Frame.ext
  · simp only [step,rescale]
    ring
  · simp only [step,rescale]
    ring
  · simp only [step,rescale]
    ring

theorem undo_homogeneous (qi h t r : F) (x : Frame F) :
    undo qi h t (rescale r x) = rescale r (undo qi h t x) := by
  apply Frame.ext
  · simp only [undo,rescale]
    ring
  · simp only [undo,rescale]
    ring
  · simp only [undo,rescale]
    ring

theorem rescale_inverse (r c : F) (h : c*r=1) (x : Frame F) :
    rescale c (rescale r x) = x := by
  apply Frame.ext
  · simp only [rescale]
    rw [← mul_assoc,h,one_mul]
  · simp only [rescale]
    rw [← mul_assoc,h,one_mul]
  · simp only [rescale]
    calc c^2*(r^2*x.l) = (c*r)^2*x.l := by ring
      _ = x.l := by rw [h,one_pow,one_mul]

noncomputable def gauge (n d : F) : F := by
  classical
  exact if d=0 then n else d

theorem gauge_nonzero (n d : F) (h : n ≠ 0 ∨ d ≠ 0) :
    gauge n d ≠ 0 := by
  classical
  by_cases hd : d=0
  · have hn : n ≠ 0 := h.resolve_right (fun hn => hn hd)
    simp [gauge,hd,hn]
  · simp [gauge,hd]

theorem first_step (q h t n l : F) :
    step q h t (⟨n,1,l⟩ : Frame F) = ⟨q,n+h,q*(l+t)⟩ := by
  simp [step]

/-- An inverse-certified sequence is sufficient for exact recomputation.
    The native source must separately establish each concrete step contract. -/
structure RStep (A : Type*) where
  run : A → A
  back : A → A
  left_inv : ∀ a, back (run a)=a

def forward {A : Type*} : List (RStep A) → A → A
  | [], a => a
  | s::ss, a => forward ss (s.run a)

def backward {A : Type*} : List (RStep A) → A → A
  | [], a => a
  | s::ss, a => s.back (backward ss a)

theorem sequence_inverse {A : Type*} (ss : List (RStep A)) (a : A) :
    backward ss (forward ss a)=a := by
  induction ss generalizing a with
  | nil => rfl
  | cons s ss ih => simp [forward,backward,ih,s.left_inv]

/-- The phase function of a recomputed coordinate equals its original
    value; its HMR measurement result is universally quantified. -/
theorem replay_debt (m phase old replay : Bool) (h : old=replay) :
    Bool.xor (Bool.xor phase (m && old)) (m && replay) = phase := by
  subst replay
  cases m <;> cases phase <;> cases old <;> decide

theorem two_debts (m n phase a b : Bool) :
    Bool.xor (Bool.xor (Bool.xor (Bool.xor phase (m && a)) (n && b))
      (m && a)) (n && b) = phase := by
  cases m <;> cases n <;> cases phase <;> cases a <;> cases b <;> decide

end GVQCC.NoCopy
#print axioms GVQCC.NoCopy.step_inverse
#print axioms GVQCC.NoCopy.step_homogeneous
#print axioms GVQCC.NoCopy.undo_homogeneous
#print axioms GVQCC.NoCopy.rescale_inverse
#print axioms GVQCC.NoCopy.gauge_nonzero
#print axioms GVQCC.NoCopy.first_step
#print axioms GVQCC.NoCopy.sequence_inverse
#print axioms GVQCC.NoCopy.replay_debt
#print axioms GVQCC.NoCopy.two_debts
