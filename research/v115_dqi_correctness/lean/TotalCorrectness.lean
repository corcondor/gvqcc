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
  · simp [step, hn]

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

namespace GVQCC.V115.Adaptive

open Polynomial

/-- The all-zero finite-chart case is not an exceptional failure: the degree
    of the numerator saturates the remaining degree budget.  The divisibility
    premise is the product of the distinct remaining irreducible quadratics;
    that premise must be proved by the concrete chart implementation. -/
theorem saturated_degree {F : Type*} [Field F]
    (P N : Polynomial F) (m : ℕ)
    (hn : N ≠ 0) (hdiv : P ∣ N)
    (hl : m ≤ P.natDegree) (hu : N.natDegree ≤ m) :
    N.natDegree = m := by
  have h := Polynomial.natDegree_le_of_dvd hdiv hn
  omega

theorem finite_budget (m dn dd dh dr : ℕ)
    (hm : 0 < m) (hn : dn ≤ m) (hd : dd ≤ m+1)
    (hh : dh ≤ 1)
    (hr : dr = 0 ∨ dr+2 ≤ max dd (dh+dn)) :
    dr ≤ m-1 := by
  have hmax : max dd (dh+dn) ≤ m+1 := max_le hd (by omega)
  omega

theorem infinity_budget (m dn dd dq dr : ℕ)
    (hm : 0 < m) (hn : dn = m) (hd : dd ≤ m+1)
    (hq : dq = 0 ∨ dq+dn ≤ dd)
    (hr : dr = 0 ∨ dr < dn) :
    dq ≤ 1 ∧ dr ≤ m-1 := by
  omega

inductive Pivot (R : Type*) where
  | finite (g h : R)
  | infinity (q : R)
  | stop

variable {R : Type*} [CommRing R]

def restore : Pivot R → R × R → R × R
  | .finite g h, (a,b) => (b, g*a+h*b)
  | .infinity q, (a,b) => (b, a+q*b)
  | .stop, s => s

/-- Exact algebraic contract of each forward pivot, including the stop case.
    Coefficients are in characteristic two for the DQI specialization. -/
def ValidStep : Pivot R → R × R → R × R → Prop
  | .finite g h, (n,d), (a,b) => b=n ∧ d=g*a+h*n
  | .infinity q, (n,d), (a,b) => b=n ∧ d=a+q*n
  | .stop, s,t => t=s

theorem adaptive_step_inverse (p : Pivot R) (s t : R × R)
    (hs : ValidStep p s t) : restore p t = s := by
  rcases s with ⟨n,d⟩
  rcases t with ⟨a,b⟩
  cases p with
  | finite g h =>
    change b=n ∧ d=g*a+h*n at hs
    rcases hs with ⟨hb,hd⟩
    simp [restore, hb, hd]
  | infinity q =>
    change b=n ∧ d=a+q*n at hs
    rcases hs with ⟨hb,hd⟩
    simp [restore, hb, hd]
  | stop =>
    exact hs

inductive ValidTrace : List (Pivot R) → R × R → R × R → Prop
  | nil (s : R × R) : ValidTrace [] s s
  | cons {p ps s t u} : ValidStep p s t →
      ValidTrace ps t u → ValidTrace (p::ps) s u

def recover : List (Pivot R) → R × R → R × R
  | [], s => s
  | p::ps, s => restore p (recover ps s)

theorem adaptive_trace_inverse (ps : List (Pivot R)) (s t : R × R)
    (h : ValidTrace ps s t) : recover ps t = s := by
  induction h with
  | nil s => rfl
  | cons hstep htrace ih =>
    simp only [recover, ih]
    exact adaptive_step_inverse _ _ _ hstep

end GVQCC.V115.Adaptive

#print axioms GVQCC.V115.Adaptive.saturated_degree
#print axioms GVQCC.V115.Adaptive.finite_budget
#print axioms GVQCC.V115.Adaptive.infinity_budget
#print axioms GVQCC.V115.Adaptive.adaptive_trace_inverse

namespace GVQCC.V115.Spec

open scoped BigOperators
open Polynomial

variable {F : Type*} [Field F]

/-- Actual legal inputs: at most 35 nonzero magnitudes on nonzero field points. -/
noncomputable def support (D : Finset F) (e : F → F) : Finset F := by
  classical
  exact D.filter (fun x => e x ≠ 0)

def Legal (D : Finset F) (e : F → F) : Prop :=
  (support D e).card ≤ 35 ∧ ∀ x, x ∉ D → e x = 0

def syndrome (D : Finset F) (e : F → F) (j : Fin 70) : F :=
  ∑ x ∈ D, e x * x^(j.val+1)

theorem support_subset (D : Finset F) (e : F → F) :
    support D e ⊆ D := by
  classical
  exact Finset.filter_subset _ _

theorem outside_support_zero (D : Finset F) (e : F → F) (x : F)
    (hx : x ∈ D) (h : x ∉ support D e) : e x = 0 := by
  classical
  by_contra he
  exact h (by simp [support, hx, he])

theorem legal_injective (D : Finset F) (hnz : ∀ x ∈ D, x ≠ 0)
    (a b : F → F) (ha : Legal D a) (hb : Legal D b)
    (h : syndrome D a = syndrome D b) : a = b := by
  classical
  let U := support D a ∪ support D b
  have hsub : U ⊆ D := Finset.union_subset (support_subset D a) (support_subset D b)
  have hc : U.card ≤ 70 := by
    have hle := Finset.card_union_le (support D a) (support D b)
    have h1 := ha.1
    have h2 := hb.1
    change (support D a ∪ support D b).card ≤ 70
    omega
  have hza : ∀ x, x ∉ U → a x = 0 := by
    intro x hx
    by_cases hd : x ∈ D
    · apply outside_support_zero D a x hd
      intro hs
      exact hx (Finset.mem_union.mpr (Or.inl hs))
    · exact ha.2 x hd
  have hzb : ∀ x, x ∉ U → b x = 0 := by
    intro x hx
    by_cases hd : x ∈ D
    · apply outside_support_zero D b x hd
      intro hs
      exact hx (Finset.mem_union.mpr (Or.inr hs))
    · exact hb.2 x hd
  have hm : ∀ j : ℕ, j < 70 →
      (∑ x ∈ U, a x*x^(j+1)) = (∑ x ∈ U, b x*x^(j+1)) := by
    intro j hj
    have he := congrFun h (⟨j,hj⟩ : Fin 70)
    change (∑ x ∈ D, a x*x^(j+1)) = (∑ x ∈ D, b x*x^(j+1)) at he
    have hsa : (∑ x ∈ U, a x*x^(j+1)) = ∑ x ∈ D, a x*x^(j+1) :=
      Finset.sum_subset hsub (fun x _ hx => by simp [hza x hx])
    have hsb : (∑ x ∈ U, b x*x^(j+1)) = ∑ x ∈ D, b x*x^(j+1) :=
      Finset.sum_subset hsub (fun x _ hx => by simp [hzb x hx])
    exact hsa.trans (he.trans hsb.symm)
  funext x
  by_cases hx : x ∈ U
  · exact GVQCC.V115.dqi70_unique U a b hc (fun y hy => hnz y (hsub hy)) hm x hx
  · rw [hza x hx, hzb x hx]

/-- Noncomputable specification only: no claim of an efficient implementation. -/
noncomputable def decodeSpec (D : Finset F) (s : Fin 70 → F) : Option (F → F) := by
  classical
  exact if h : ∃ e, Legal D e ∧ syndrome D e = s then some (Classical.choose h) else none

theorem decodeSpec_correct (D : Finset F) (hnz : ∀ x ∈ D, x ≠ 0)
    (e : F → F) (he : Legal D e) : decodeSpec D (syndrome D e) = some e := by
  classical
  have hex : ∃ a, Legal D a ∧ syndrome D a = syndrome D e := ⟨e,he,rfl⟩
  have hchoose := Classical.choose_spec hex
  have heq := legal_injective D hnz (Classical.choose hex) e hchoose.1 he hchoose.2
  simp [decodeSpec, hex, heq]

theorem decoder_refinement (D : Finset F) (hnz : ∀ x ∈ D, x ≠ 0)
    (dec : (Fin 70 → F) → Option (F → F))
    (h : ∀ e, Legal D e → ∃ a, dec (syndrome D e) = some a ∧
      Legal D a ∧ syndrome D a = syndrome D e)
    (e : F → F) (he : Legal D e) :
    dec (syndrome D e) = some e := by
  obtain ⟨a,ha,hal,has⟩ := h e he
  have heq := legal_injective D hnz a e hal he has
  rw [ha, heq]

/-- A recurrence kernel in moment form forces a root at every nonzero error.
    This statement does not assume any leading moment is nonzero. -/
theorem moment_kernel_roots (S : Finset F) (a : F → F) (p : Polynomial F)
    (ha : ∀ x ∈ S, a x ≠ 0) (hx : ∀ x ∈ S, x ≠ 0)
    (hk : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, (a x * x * p.eval x) * x^k) = 0) :
    ∀ x ∈ S, p.eval x = 0 := by
  intro x hxs
  have hz := GVQCC.V115.moments_injective S (fun x => a x * x * p.eval x) hk x hxs
  exact (mul_eq_zero.mp hz).resolve_left (mul_ne_zero (ha x hxs) (hx x hxs))

/-- The square Hankel kernel contains no nonzero degree < w polynomial.
    In particular leading-zero moments do not justify an early stop. -/
theorem hankel_kernel_trivial (S : Finset F) (a : F → F) (p : Polynomial F)
    (ha : ∀ x ∈ S, a x ≠ 0) (hx : ∀ x ∈ S, x ≠ 0)
    (hp : p.natDegree < S.card)
    (hk : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, (a x * x * p.eval x) * x^k) = 0) : p = 0 :=
  Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' p S
    (moment_kernel_roots S a p ha hx hk) hp

/-- A checked sparse decoder yields the right *abstract* phase. Physical
    cleanup and measurement-instrument semantics require separate proofs. -/
theorem decoder_phase_refinement (D : Finset F) (hnz : ∀ x ∈ D, x ≠ 0)
    (e a : F → F) (he : Legal D e) (ha : Legal D a)
    (hs : syndrome D a = syndrome D e) (phase : (F → F) → Bool) :
    phase a = phase e := by
  rw [legal_injective D hnz a e ha he hs]

end GVQCC.V115.Spec

#print axioms GVQCC.V115.Spec.legal_injective
#print axioms GVQCC.V115.Spec.decodeSpec_correct
#print axioms GVQCC.V115.Spec.decoder_refinement
#print axioms GVQCC.V115.Spec.moment_kernel_roots
#print axioms GVQCC.V115.Spec.hankel_kernel_trivial
#print axioms GVQCC.V115.Spec.decoder_phase_refinement

namespace GVQCC.V115.PolynomialCharts
open Polynomial
open scoped BigOperators
variable {F : Type*} [Field F]

/-- Distinct quadratic interpolation nodes are pairwise coprime, even
    without an irreducibility assumption. -/
def quad (k : F) : Polynomial F := X^2 + X + C k

theorem quad_coprime (a b : F) (hab : a ≠ b) :
    IsCoprime (quad a) (quad b) := by
  refine ⟨C ((a-b)⁻¹), -C ((a-b)⁻¹), ?_⟩
  calc
    C ((a-b)⁻¹) * quad a + -C ((a-b)⁻¹) * quad b =
      C ((a-b)⁻¹) * (quad a - quad b) := by ring
    _ = C ((a-b)⁻¹) * C (a-b) := by
      rw [map_sub]
      unfold quad
      ring
    _ = 1 := by rw [← map_mul, inv_mul_cancel₀ (sub_ne_zero.mpr hab), map_one]

theorem coprime_node_product (a : F) (S : Finset F) (ha : a ∉ S) :
    IsCoprime (quad a) (∏ b ∈ S, quad b) := by
  classical
  induction S using Finset.induction_on with
  | empty => simp
  | @insert b S hb ih =>
    rw [Finset.prod_insert hb]
    have hab : a ≠ b := by
      intro h
      apply ha
      simp [h]
    have has : a ∉ S := by
      intro h
      exact ha (Finset.mem_insert_of_mem h)
    exact (quad_coprime a b hab).mul_right (ih has)

theorem all_nodes_product_dvd (S : Finset F) (N : Polynomial F)
    (h : ∀ k ∈ S, quad k ∣ N) :
    (∏ k ∈ S, quad k) ∣ N := by
  classical
  induction S using Finset.induction_on with
  | empty => simp
  | @insert k S hk ih =>
    rw [Finset.prod_insert hk]
    exact (coprime_node_product k S hk).mul_dvd
      (h k (Finset.mem_insert_self k S))
      (ih (fun j hj => h j (Finset.mem_insert_of_mem hj)))

theorem quad_degree (a : F) : (quad a).natDegree = 2 := by
  have h : (X + C a : Polynomial F).natDegree ≤ 1 := by
    have h' := Polynomial.natDegree_add_le (X : Polynomial F) (C a)
    simpa using h'
  have hl : (X + C a : Polynomial F).natDegree < (X^2 : Polynomial F).natDegree := by
    simp
    omega
  have he := Polynomial.natDegree_add_eq_left_of_natDegree_lt hl
  simpa [quad, add_assoc] using he

/-- The actual polynomial saturation result, rather than assuming that
    the product of all distinct nodes divides N. The multiplicity bound
    on the remaining slot schedule is still a separate obligation. -/
theorem all_poles_saturate (S : Finset F) (N : Polynomial F) (m : ℕ)
    (hn : N ≠ 0) (hslots : m ≤ 2*S.card) (hcap : N.natDegree ≤ m)
    (h : ∀ k ∈ S, quad k ∣ N) : N.natDegree = m := by
  classical
  have hp := all_nodes_product_dvd S N h
  have hnon : ∀ k ∈ S, quad k ≠ 0 := by
    intro k _
    intro he
    have hd := quad_degree k
    rw [he, Polynomial.natDegree_zero] at hd
    omega
  have hdeg : (∏ k ∈ S, quad k).natDegree = 2*S.card := by
    rw [Polynomial.natDegree_prod S quad hnon]
    simp [quad_degree, Nat.mul_comm]
  have hle := Polynomial.natDegree_le_of_dvd hp hn
  omega

/-- Derive the actual finite-pivot degree bounds from a polynomial identity,
    not from the numerical degree bound as a hypothesis. -/
theorem finite_polynomial_budget (m : ℕ) (N D A g h : Polynomial F)
    (hm : 0 < m) (hn : N.natDegree ≤ m) (hd : D.natDegree ≤ m+1)
    (hg : g.natDegree = 2) (hh : h.natDegree ≤ 1)
    (he : D = g*A + h*N) : A.natDegree ≤ m-1 := by
  by_cases ha : A = 0
  · simp [ha]
  have hg0 : g ≠ 0 := by
    intro hz
    rw [hz, Polynomial.natDegree_zero] at hg
    omega
  have hmul := Polynomial.natDegree_mul hg0 ha
  have hidentity : g*A = D - h*N := by rw [he]; ring
  have hsub := Polynomial.natDegree_sub_le D (h*N)
  rw [← hidentity, hmul, hg] at hsub
  have hprod := Polynomial.natDegree_mul_le (p := h) (q := N)
  have hmax : max D.natDegree (h*N).natDegree ≤ m+1 := max_le hd (by omega)
  omega

end GVQCC.V115.PolynomialCharts
#print axioms GVQCC.V115.PolynomialCharts.quad_coprime
#print axioms GVQCC.V115.PolynomialCharts.all_nodes_product_dvd
#print axioms GVQCC.V115.PolynomialCharts.all_poles_saturate
#print axioms GVQCC.V115.PolynomialCharts.finite_polynomial_budget
