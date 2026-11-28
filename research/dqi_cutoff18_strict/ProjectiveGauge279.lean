import Mathlib
namespace GVQCC.ProjectiveGauge279
def update (g a b : Bool) : Bool :=
  let d := Bool.xor a b
  Bool.xor (if d then false else Bool.xor g a) a
def lexStep (g : Bool) (p : Bool × Bool) : Bool :=
  if p.1 = p.2 then g else p.1
theorem update_exact (g a b : Bool) :
    update g a b = lexStep g (a,b) := by
  cases g <;> cases a <;> cases b <;> decide
theorem word_compare (xs : List (Bool × Bool)) (g : Bool) :
    xs.foldl (fun c p => update c p.1 p.2) g = xs.foldl lexStep g := by
  induction xs generalizing g with
  | nil => rfl
  | cons p ps ih =>
      simp only [List.foldl_cons, update_exact]
def exchange (g a b : Bool) : Bool × Bool :=
  let d := Bool.xor a b
  let a' := if g then Bool.xor a d else a
  (a', Bool.xor d a')
theorem exchange_exact (g a b : Bool) :
    exchange g a b = if g then (b,a) else (a,b) := by
  cases g <;> cases a <;> cases b <;> decide

section Field
variable {F : Type*} [Field F]
theorem line_shear (r t c d u : F) :
    r + (t+d*u) + c*u = (r+t)+(c+d)*u := by ring
theorem anchor_zero (t d u : F) (h2 : (2:F)=0) :
    t+(t+d*u)+d*u=0 := by
  calc
    _ = 2*(t+d*u) := by ring
    _ = _ := by rw [h2, zero_mul]
theorem slope_equiv (r t c d u : F) (h : c+d ≠ 0) :
    (r+t)/(c+d)=u ↔ r+t=(c+d)*u := by
  rw [div_eq_iff h, mul_comm u (c+d)]
end Field

theorem score_recover (k : ℕ) (hk : 0 < k) (b : Bool) :
    k-1+(if b then 1 else 0)+1=k+(if b then 1 else 0) := by omega
theorem count_lower_bound (n : ℕ) : n % 64 ≤ n := Nat.mod_le _ _
theorem strict_candidate_safe (n s : ℕ) (h : s < n % 64) : s < n :=
  lt_of_lt_of_le h (count_lower_bound n)
theorem root_budget (N n s : ℕ) (hs : s < n) (hn : n+1 ≤ N) :
    11*(N-(n+1))+11 < 11*(N-s) := by omega
theorem sorter_reduction : 13759499-10444726=3314773 := by decide
theorem full_instruction_reduction : 67549292-67528845=20447 := by decide

#print axioms update_exact
#print axioms word_compare
#print axioms exchange_exact
#print axioms line_shear
#print axioms anchor_zero
#print axioms slope_equiv
#print axioms score_recover
#print axioms count_lower_bound
#print axioms strict_candidate_safe
#print axioms root_budget
#print axioms sorter_reduction
#print axioms full_instruction_reduction
end GVQCC.ProjectiveGauge279
