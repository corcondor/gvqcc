import Mathlib

namespace DQI898

variable {F : Type*} [Field F]

-- Subtraction is XOR in characteristic two.  These are the exact scalar
-- identities used in the narrow slot33 chart, stated over any field.
def slope (p q v : F) : F := 1 + p * v / q
def guardPoly (p q a c d : F) : F := q * d^2 + p * c * d - p^2 * a

theorem guard_factor (p q a c d : F) (hq : q ≠ 0) (hd : d ≠ 0) :
    guardPoly p q a c d = q * d^2 * slope p q ((c - p * (a/d))/d) := by
  unfold guardPoly slope
  field_simp [hq, hd] <;> ring

theorem guard_iff (p q a c d : F) (hq : q ≠ 0) (hd : d ≠ 0) :
    guardPoly p q a c d = 0 ↔ slope p q ((c - p * (a/d))/d) = 0 := by
  rw [guard_factor p q a c d hq hd]
  constructor
  · intro h
    exact (mul_eq_zero.mp h).resolve_left (mul_ne_zero hq (pow_ne_zero 2 hd))
  · intro h
    rw [h, mul_zero]

theorem guard_xor (p q a c d : F) (h2 : (2 : F) = 0) :
    q*d^2 + p*c*d + p^2*a = guardPoly p q a c d := by
  unfold guardPoly
  calc
    _ = q*d^2 + p*c*d - p^2*a + 2*(p^2*a) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem ratio_xor (c p u : F) (h2 : (2 : F) = 0) :
    c+p*u = c-p*u := by
  calc
    _ = c-p*u+2*(p*u) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem ratio_recover (u v d p : F) (hd : d ≠ 0) :
    u*d/d = u ∧ ((v*d+p*u)-p*(u*d/d))/d = v := by
  constructor
  · exact mul_div_cancel_right₀ u hd
  · rw [mul_div_cancel_right₀ u hd]
    field_simp [hd] <;> ring

theorem shear_identity (p q u v d : F) :
    d + p*(v*d+p*u)/q = slope p q v*d + p^2*u/q := by
  simp only [slope, div_eq_mul_inv]
  ring

theorem recover_low (C u v : F) (hC : C ≠ 0) (hu : u ≠ 0) :
    C/(C/u) = u ∧ C*(v*(C/u)^2/C)/(C/u)^2 = v := by
  have hx : C/u ≠ 0 := div_ne_zero hC hu
  constructor
  · field_simp [hC, hu] <;> ring
  · field_simp [hC, hx] <;> ring

def forward (p q C u v d : F) : F × F × F :=
  (C/u, v*(C/u)^2/C, slope p q v*d + p^2*u/q)

def backward (p q C : F) (x : F × F × F) : F × F × F :=
  let u := C/x.1
  let v := C*x.2.1/x.1^2
  (u,v,(x.2.2-p^2*u/q)/slope p q v)

theorem chart_roundtrip (p q C u v d : F) (hC : C ≠ 0) (hu : u ≠ 0)
    (hf : slope p q v ≠ 0) :
    backward p q C (forward p q C u v d) = (u,v,d) := by
  obtain ⟨hU,hV⟩ := recover_low C u v hC hu
  have hD : (slope p q v*d + p^2*u/q - p^2*u/q)/slope p q v = d := by
    rw [add_sub_cancel_right, mul_comm (slope p q v) d, mul_div_cancel_right₀ d hf]
  unfold backward forward
  dsimp
  rw [hU,hV,hD]

-- The missing stratum has a genuine collision in the *local coordinate map*.
-- This is not a claim that both abstract states are reachable in the decoder.
theorem singular_collision (p q C u v d₁ d₂ : F)
    (hf : slope p q v = 0) (hd : d₁ ≠ d₂) :
    forward p q C u v d₁ = forward p q C u v d₂ ∧
      (u,v,d₁) ≠ (u,v,d₂) := by
  constructor
  · simp [forward, hf]
  · intro h
    exact hd (congrArg (fun x : F × F × F => x.2.2) h)

-- Proposed self-describing coordinate chart.  The zero-slope case retains
-- d instead of a non-injective shear.  The branch is reconstructible from v.
-- It needs a modified downstream polynomial consumer, not just a guard edit.
noncomputable def hybridForward (p q C u v d : F) : F × F × F := by
  classical
  exact (C/u, v*(C/u)^2/C,
    if slope p q v = 0 then d else slope p q v*d + p^2*u/q)

noncomputable def hybridBackward (p q C : F) (x : F × F × F) : F × F × F := by
  classical
  exact
    let u := C/x.1
    let v := C*x.2.1/x.1^2
    (u,v,if slope p q v = 0 then x.2.2 else (x.2.2-p^2*u/q)/slope p q v)

theorem hybrid_roundtrip (p q C u v d : F) (hC : C ≠ 0) (hu : u ≠ 0) :
    hybridBackward p q C (hybridForward p q C u v d) = (u,v,d) := by
  classical
  obtain ⟨hU,hV⟩ := recover_low C u v hC hu
  unfold hybridBackward hybridForward
  dsimp
  rw [hU,hV]
  by_cases hf : slope p q v = 0
  · simp [hf]
  · have hD : (slope p q v*d + p^2*u/q - p^2*u/q)/slope p q v = d := by
      rw [add_sub_cancel_right, mul_comm (slope p q v) d, mul_div_cancel_right₀ d hf]
    simp [hf,hD]

theorem hmr_cancel (m f phase : Bool) :
    Bool.xor (Bool.xor phase (m && f)) (m && f) = phase := by
  cases m <;> cases f <;> cases phase <;> decide

theorem guard_xor_uncompute (g f : Bool) :
    Bool.xor (Bool.xor g f) f = g := by
  cases g <;> cases f <;> decide

end DQI898

#print axioms DQI898.guard_factor
#print axioms DQI898.guard_iff
#print axioms DQI898.guard_xor
#print axioms DQI898.ratio_xor
#print axioms DQI898.ratio_recover
#print axioms DQI898.shear_identity
#print axioms DQI898.recover_low
#print axioms DQI898.chart_roundtrip
#print axioms DQI898.singular_collision
#print axioms DQI898.hybrid_roundtrip
#print axioms DQI898.hmr_cancel
#print axioms DQI898.guard_xor_uncompute
