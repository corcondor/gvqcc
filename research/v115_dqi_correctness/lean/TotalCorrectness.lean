import Mathlib

/-!
V115 DQI specification, not a certificate of the existing KMB.
The chart interface explicitly requires a residue-field section and exact division.
The sparse uniqueness theorem is independent of the chart and of any decoder.
-/
namespace GVQCC.V115

set_option autoImplicit false

structure Chart (R K : Type*) [CommRing R] [Field K] where
  g : R
  res : R →+* K
  lift : K → R
  divG : R → R
  res_g : res g = 0
  res_lift : ∀ h, res (lift h) = h
  exact_div : ∀ x, res x = 0 → g * divG x = x

inductive Head (K : Type*) where
  | zero
  | regular (h : K)

section Charts
variable {R K : Type*} [CommRing R] [Field K]

noncomputable def step (C : Chart R K) (s : R × R) : (R × R) × Head K := by
  classical
  exact if C.res s.1 = 0 then
    ((C.divG s.1, s.2), Head.zero)
  else
    let h := C.res s.2 / C.res s.1
    ((C.divG (s.2 - C.lift h * s.1), s.1), Head.regular h)

def undo (C : Chart R K) (s : R × R) (h : Head K) : R × R :=
  match h with
  | .zero => (C.g * s.1, s.2)
  | .regular h => (s.2, C.g * s.1 + C.lift h * s.2)

theorem singular_regular_impossible (C : Chart R K) (n d h m : R)
    (hn : C.res n = 0) (hd : C.res d ≠ 0) :
    d - h*n ≠ C.g*m := by
  intro he
  have hr := congrArg (fun x => C.res x) he
  simp [hn, C.res_g] at hr
  exact hd hr

theorem regular_divisible (C : Chart R K) (n d : R)
    (hn : C.res n ≠ 0) :
    C.res (d - C.lift (C.res d / C.res n) * n) = 0 := by
  rw [map_sub, map_mul, C.res_lift, div_mul_cancel₀ _ hn, sub_self]

theorem undo_step (C : Chart R K) (s : R × R) :
    undo C (step C s).1 (step C s).2 = s := by
  classical
  rcases s with ⟨n,d⟩
  by_cases hn : C.res n = 0
  · simp [step, hn, undo, C.exact_div n hn]
  · have hdiv := C.exact_div _ (regular_divisible C n d hn)
    simp [step, hn, undo, hdiv]

def Bezout (n d : R) : Prop := ∃ a b : R, a*n + b*d = 1

theorem bezout_residue (C : Chart R K) (n d : R)
    (hb : Bezout n d) (hn : C.res n = 0) : C.res d ≠ 0 := by
  rintro hd
  obtain ⟨a,b,he⟩ := hb
  have hr := congrArg (fun x => C.res x) he
  simp [hn, hd] at hr

theorem bezout_after_undo (C : Chart R K) (s : R × R) (h : Head K)
    (hb : Bezout (undo C s h).1 (undo C s h).2) :
    Bezout s.1 s.2 := by
  rcases s with ⟨n,d⟩
  cases h with
  | zero =>
    obtain ⟨a,b,he⟩ := hb
    change a*(C.g*n) + b*d = 1 at he
    exact ⟨a*C.g,b,by linear_combination he⟩
  | regular h =>
    obtain ⟨a,b,he⟩ := hb
    change a*d + b*(C.g*n + C.lift h*d) = 1 at he
    exact ⟨b*C.g,a+b*C.lift h,by linear_combination he⟩

theorem bezout_preserved (C : Chart R K) (s : R × R)
    (hb : Bezout s.1 s.2) :
    Bezout (step C s).1.1 (step C s).1.2 := by
  apply bezout_after_undo C (step C s).1 (step C s).2
  rw [undo_step]
  exact hb

theorem next_denominator_unit (C : Chart R K) (s : R × R)
    (hb : Bezout s.1 s.2) : C.res (step C s).1.2 ≠ 0 := by
  classical
  rcases s with ⟨n,d⟩
  by_cases hn : C.res n = 0
  · simpa [step, hn] using bezout_residue C n d hb hn
  · simpa [step, hn] using hn

def storedValue (h : Head K) : K :=
  match h with
  | .zero => 0
  | .regular a => a

/-- Head=0 identifies the zero chart ONLY with a unit denominator on entry. -/
theorem head_zero_iff (C : Chart R K) (s : R × R)
    (hd : C.res s.2 ≠ 0) :
    storedValue (step C s).2 = 0 ↔ C.res s.1 = 0 := by
  classical
  rcases s with ⟨n,d⟩
  by_cases hn : C.res n = 0
  · simp [step, hn, storedValue]
  · simp [step, hn, storedValue, div_ne_zero hd hn]

/-- Multi-node packing, with an explicit typed branch record. -/
noncomputable def pack (cs : List (Chart R K)) (s : R × R) :
    (R × R) × List (Chart R K × Head K) :=
  match cs with
  | [] => (s, [])
  | c::cs =>
    let v := step c s
    let p := pack cs v.1
    (p.1, p.2 ++ [(c, v.2)])

def unpack (s : R × R) (hs : List (Chart R K × Head K)) : R × R :=
  match hs with
  | [] => s
  | v::vs => unpack (undo v.1 s v.2) vs

theorem unpack_append (s : R × R) (a b : List (Chart R K × Head K)) :
    unpack s (a ++ b) = unpack (unpack s a) b := by
  induction a generalizing s with
  | nil => rfl
  | cons x xs ih => simp [unpack, ih]

theorem pack_roundtrip (cs : List (Chart R K)) (s : R × R) :
    unpack (pack cs s).1 (pack cs s).2 = s := by
  induction cs generalizing s with
  | nil => rfl
  | cons c cs ih =>
    simp only [pack, unpack_append, ih, unpack, undo_step]

end Charts

section Moments
variable {F : Type*} [Field F]

/-- Exact Vandermonde injectivity by eliminating one support point at a time. -/
theorem moments_injective (s : Finset F) (a : F → F)
    (h : ∀ k : ℕ, k < s.card → (∑ x ∈ s, a x * x^k) = 0) :
    ∀ x ∈ s, a x = 0 := by
  classical
  induction s using Finset.induction_on generalizing a with
  | empty => simp
  | @insert b s hb ih =>
    have hs : ∀ k : ℕ, k < s.card →
        (∑ y ∈ s, (a y * (y-b))*y^k) = 0 := by
      intro k hk
      have h0 := h k (by rw [Finset.card_insert_of_notMem hb]; omega)
      have h1 := h (k+1) (by rw [Finset.card_insert_of_notMem hb]; omega)
      rw [Finset.sum_insert hb] at h0 h1
      calc
        (∑ y ∈ s, (a y * (y-b))*y^k) =
            (∑ y ∈ s, a y * y^(k+1)) - b*(∑ y ∈ s, a y * y^k) := by
          rw [Finset.mul_sum, ← Finset.sum_sub_distrib]
          apply Finset.sum_congr rfl
          intro y _
          rw [pow_succ]
          ring
        _ = 0 := by
          rw [pow_succ b] at h1
          linear_combination h1 - b*h0
    have hz := ih (fun y => a y*(y-b)) hs
    have hrest : ∀ x ∈ s, a x = 0 := by
      intro x hx
      have hne : x-b ≠ 0 := sub_ne_zero.mpr (by
        intro he
        subst x
        exact hb hx)
      exact (mul_eq_zero.mp (hz x hx)).resolve_right hne
    have hsum : (∑ x ∈ s, a x*x^0) = 0 := Finset.sum_eq_zero
      (fun x hx => by simp [hrest x hx])
    have h0 := h 0 (by rw [Finset.card_insert_of_notMem hb]; omega)
    rw [Finset.sum_insert hb, hsum] at h0
    have hab : a b = 0 := by simpa using h0
    intro x hx
    rcases Finset.mem_insert.mp hx with rfl | hx
    · exact hab
    · exact hrest x hx

/-- Syndrome equality on a union of at most 70 nonzero evaluation points
forces equality of the error magnitudes. It is the decoder admission contract,
not a proof that a particular decoder always produces such a certificate. -/
theorem dqi70_unique (s : Finset F) (a b : F → F) (hc : s.card ≤ 70)
    (hnz : ∀ x ∈ s, x ≠ 0)
    (h : ∀ j : ℕ, j < 70 →
      (∑ x ∈ s, a x*x^(j+1)) = (∑ x ∈ s, b x*x^(j+1))) :
    ∀ x ∈ s, a x = b x := by
  classical
  have hm : ∀ k : ℕ, k < s.card →
      (∑ x ∈ s, ((a x-b x)*x)*x^k) = 0 := by
    intro k hk
    have he := h k (by omega)
    calc
      (∑ x ∈ s, ((a x-b x)*x)*x^k) =
          (∑ x ∈ s, a x*x^(k+1)) - (∑ x ∈ s, b x*x^(k+1)) := by
        rw [← Finset.sum_sub_distrib]
        apply Finset.sum_congr rfl
        intro x _
        rw [pow_succ]
        ring
      _ = 0 := sub_eq_zero.mpr he
  intro x hx
  exact sub_eq_zero.mp ((mul_eq_zero.mp
    (moments_injective s (fun x => (a x-b x)*x) hm x hx)).resolve_right (hnz x hx))

/-- For two certified sparse error vectors extended by zero outside the union,
any phase function of the complete error vector is the same. -/
theorem certified_phase (s : Finset F) (a b : F → F)
    (ha : ∀ x, x ∉ s → a x = 0) (hb : ∀ x, x ∉ s → b x = 0)
    (hc : s.card ≤ 70) (hnz : ∀ x ∈ s, x ≠ 0)
    (h : ∀ j : ℕ, j < 70 →
      (∑ x ∈ s, a x*x^(j+1)) = (∑ x ∈ s, b x*x^(j+1)))
    (phase : (F → F) → Bool) : phase a = phase b := by
  classical
  have he : a = b := by
    funext x
    by_cases hx : x ∈ s
    · exact dqi70_unique s a b hc hnz h x hx
    · rw [ha x hx, hb x hx]
  rw [he]

end Moments

/-- Local measurement phase accounting; actual physical transport must
establish that the Boolean function f remains available at cleanup. -/
theorem hmr_debt_cancel (m f p : Bool) :
    Bool.xor (Bool.xor p (m && f)) (m && f) = p := by
  cases m <;> cases f <;> cases p <;> decide

end GVQCC.V115

#print axioms GVQCC.V115.singular_regular_impossible
#print axioms GVQCC.V115.pack_roundtrip
#print axioms GVQCC.V115.bezout_preserved
#print axioms GVQCC.V115.head_zero_iff
#print axioms GVQCC.V115.dqi70_unique
#print axioms GVQCC.V115.certified_phase
#print axioms GVQCC.V115.hmr_debt_cancel
