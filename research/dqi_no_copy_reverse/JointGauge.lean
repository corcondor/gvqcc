import Mathlib

namespace GVQCC.JointGauge

variable {F : Type*} [CommRing F]

/-- The scalar frame has a linear recurrence in (n,d) and a Frobenius
linear recurrence in (n²,d²,l) after its head coefficients are fixed. -/
def step (q h t : F) (n d l : F) : F × F × F :=
  (q*d,n+h*d,q*(l+t*d^2))

def twoStep (q₁ q₂ h₁ h₂ t₁ t₂ : F) (n d l : F) : F × F × F :=
  (q₂*(n+h₁*d),
   h₂*n+(q₁+h₂*h₁)*d,
   q₂*q₁*l+q₂*t₂*n^2+q₂*(q₁*t₁+t₂*h₁^2)*d^2)

theorem twoStep_exact (q₁ q₂ h₁ h₂ t₁ t₂ n d l : F)
    (hc : (2:F)=0) :
    step q₂ h₂ t₂ (step q₁ h₁ t₁ n d l).1
      (step q₁ h₁ t₁ n d l).2.1 (step q₁ h₁ t₁ n d l).2.2
      = twoStep q₁ q₂ h₁ h₂ t₁ t₂ n d l := by
  have hs : (n+h₁*d)^2=n^2+h₁^2*d^2 := by
    calc
      _ = n^2+h₁^2*d^2+2*n*h₁*d := by ring
      _ = _ := by rw [hc,zero_mul,zero_mul,zero_mul,add_zero]
  apply Prod.ext
  · rfl
  · apply Prod.ext
    · simp only [step,twoStep]
      ring
    · simp only [step,twoStep,hs]
      ring

/-- Pulling a linear phase functional back through a shared product sum. -/
theorem phase_pullback (L : F →+ ZMod 2) (n d a b : F) :
    L (a*n+b*d) = L (a*n)+L (b*d) := map_add L _ _

/-- Two homogeneously rescaled scalar coordinates can share a factor. -/
theorem factor_gauge (r a b n d : F) :
    a*(r*n)+b*(r*d)=r*(a*n+b*d) := by ring

/-- A value transformation that leaves a phase witness invariant commutes
with the corresponding conditional diagonal phase, including an HMR mask. -/
theorem phase_commute {A : Type*} (g : A → A) (f : A → Bool)
    (h : ∀ x, f (g x)=f x) (m p : Bool) (x : A) :
    Bool.xor p (m && f (g x)) = Bool.xor p (m && f x) := by
  rw [h x]

theorem pool_two_masks (m₁ m₂ f p : Bool) :
    Bool.xor (Bool.xor p (m₁ && f)) (m₂ && f) =
      Bool.xor p (Bool.xor m₁ m₂ && f) := by
  cases m₁ <;> cases m₂ <;> cases f <;> cases p <;> decide

theorem pool_replay (m₁ m₂ f f' p : Bool) (h : f' = f) :
    Bool.xor (Bool.xor (Bool.xor p (m₁ && f)) (m₂ && f))
      (Bool.xor m₁ m₂ && f') = p := by
  subst f'
  cases m₁ <;> cases m₂ <;> cases f <;> cases p <;> decide

end GVQCC.JointGauge
#print axioms GVQCC.JointGauge.twoStep_exact
#print axioms GVQCC.JointGauge.phase_pullback
#print axioms GVQCC.JointGauge.factor_gauge
#print axioms GVQCC.JointGauge.phase_commute
#print axioms GVQCC.JointGauge.pool_two_masks
#print axioms GVQCC.JointGauge.pool_replay
