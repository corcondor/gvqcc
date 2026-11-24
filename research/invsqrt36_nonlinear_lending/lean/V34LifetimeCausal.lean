import Std.Tactic
namespace GVQCC.V34
def X := Bool.xor

-- A schedule is an injective assignment of event times that respects
-- its dependency edges. The following theorem concerns fixed logical
-- lifetimes, not arbitrary alternative nonlinear encodings.
def latest : List Nat → Nat
  | [] => 0
  | a :: as => max a (latest as)

theorem le_latest (bs : List Nat) (b : Nat) (hb : b ∈ bs) :
    b ≤ latest bs := by
  induction bs with
  | nil => simp at hb
  | cons a as ih =>
    rcases List.mem_cons.mp hb with h | h
    · subst b
      exact Nat.le_max_left a (latest as)
    · exact Nat.le_trans (ih h) (Nat.le_max_right a (latest as))

theorem latest_lt (bs : List Nat) (e : Nat) (hp : 0 < e)
    (h : ∀ b ∈ bs, b < e) : latest bs < e := by
  induction bs with
  | nil => exact hp
  | cons a as ih =>
    have ha : a < e := h a (by simp)
    have hs : latest as < e := ih (fun b hb => h b (by simp [hb]))
    change max a (latest as) < e
    by_cases hz : a ≤ latest as
    · simpa [Nat.max_eq_right hz] using hs
    · simpa [Nat.max_eq_left (by omega : latest as ≤ a)] using ha

-- If every allocation precedes every release, the latest allocation
-- gives a common live cut in every schedule respecting those constraints.
theorem forced_overlap (bs es : List Nat)
    (hp : ∀ e ∈ es, 0 < e)
    (h : ∀ b ∈ bs, ∀ e ∈ es, b < e) :
    ∃ t, (∀ b ∈ bs, b ≤ t) ∧ (∀ e ∈ es, t < e) := by
  refine ⟨latest bs, le_latest bs, ?_⟩
  intro e he
  exact latest_lt bs e (hp e he) (fun b hb => h b hb e he)

-- A hub compresses all cross-lifetime order obligations.
theorem hub_overlap (begin finish : Nat → Nat) (hub : Nat)
    (h0 : ∀ i, begin i ≤ hub) (h1 : ∀ i, hub < finish i) :
    ∃ t, ∀ i, begin i ≤ t ∧ t < finish i := by
  exact ⟨hub, fun i => ⟨h0 i, h1 i⟩⟩

-- Flattening stable nested guards is valid only with the version captured
-- at scope entry. Classical toggle from zero creates the conjunction.
theorem guard_snapshot (p c : Bool) :
    X false (p && c) = (p && c) := by
  cases p <;> cases c <;> decide

theorem guarded_data (p c v t : Bool) :
    X t (p && (c && v)) = X t ((p && c) && v) := by
  cases p <;> cases c <;> cases v <;> cases t <;> decide

theorem guarded_hmr (p c m f : Bool) :
    (f && !(p && c), p && (c && m && f)) =
    (f && !(p && c), (p && c) && m && f) := by
  cases p <;> cases c <;> cases m <;> cases f <;> decide

-- A source phase read commutes with an XOR write to an unrelated
-- coordinate; if it reads the written coordinate, the boundary term
-- is exactly the transported phase debt.
theorem phase_boundary (g x y d : Bool) :
    X (g && x && y) (g && X x d && y) = (g && d && y) := by
  cases g <;> cases x <;> cases y <;> cases d <;> decide

-- Actual repeated five-operation carry projection: CCX a b t with
-- clean t, CX c t, CX c a, CX a b, HMR c.
def carryProjection (a b c : Bool) : Bool × Bool × Bool :=
  (X a c, X b (X a c), X (a && b) c)

theorem carry_collision :
    carryProjection false true false = carryProjection true true true := by decide

theorem carry_not_injective :
    ¬ Function.Injective (fun (p : Bool × Bool × Bool) =>
      carryProjection p.1 p.2.1 p.2.2) := by
  intro h
  have e := h (a₁ := (false,true,false)) (a₂ := (true,true,true)) carry_collision
  cases e

-- The same logical carry can nevertheless be embedded in a reversible
-- moving frame, before restoring the transformed operand outputs.
theorem carry_decoder (a b c : Bool) :
    let t := X c (a && b)
    let ap := X a t
    (X a c, X b (X a c), t) =
      (X ap (a && b), X b (X ap (a && b)), t) := by
  cases a <;> cases b <;> cases c <;> decide

-- Independent fresh HMR of a decodable product is deterministic after
-- its phase debt is paid, for every outcome, without postselection.
theorem measured_product (a b m : Bool) :
    X (m && (a && b)) (m && a && b) = false := by
  cases a <;> cases b <;> cases m <;> decide

theorem native_receipts :
    54244 - 51001 = 3243 ∧
    5167 - 3818 = 1349 ∧
    298 - 294 = 4 ∧ 294 - 279 = 15 ∧
    23125 - 128 = 22997 ∧ 23157 - 80 = 23077 := by decide

end GVQCC.V34
