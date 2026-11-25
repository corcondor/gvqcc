import Std.Tactic
namespace GVQCC.V45

abbrev Row := Nat × (Nat → Bool)

def combination : List Row → List Bool → Nat → Bool
  | (_,f) :: rs, c :: cs, p => Bool.xor (c && f p) (combination rs cs p)
  | _, _, _ => false

def zeroAt : List Row → Nat → Prop
  | [], _ => True
  | (_,f) :: rs, p => f p = false ∧ zeroAt rs p

def triangular : List Row → Prop
  | [] => True
  | (p,f) :: rs => f p = true ∧ zeroAt rs p ∧ triangular rs

theorem combination_zeroAt (rs : List Row) (cs : List Bool) (p : Nat)
    (h : zeroAt rs p) : combination rs cs p = false := by
  induction rs generalizing cs with
  | nil => cases cs <;> rfl
  | cons r rs ih =>
    rcases r with ⟨i,f⟩
    cases cs with
    | nil => rfl
    | cons c cs =>
      change f p = false ∧ zeroAt rs p at h
      simp [combination, h.1, ih cs h.2]

theorem pivot_sketch_zero (rs : List Row) (cs : List Bool)
    (ht : triangular rs)
    (hp : ∀ r ∈ rs, combination rs cs r.1 = false) :
    ∀ p, combination rs cs p = false := by
  induction rs generalizing cs with
  | nil =>
    intro p
    cases cs <;> rfl
  | cons r rs ih =>
    rcases r with ⟨i,f⟩
    cases cs with
    | nil =>
      intro p
      rfl
    | cons c cs =>
      change f i = true ∧ zeroAt rs i ∧ triangular rs at ht
      have h := hp (i,f) (by simp)
      have hz := combination_zeroAt rs cs i ht.2.1
      have hc : c = false := by
        simpa [combination, ht.1, hz] using h
      subst c
      have htail : ∀ r ∈ rs, combination rs cs r.1 = false := by
        intro r hr
        have q := hp r (by simp [hr])
        simpa [combination] using q
      intro p
      simpa [combination] using ih cs ht.2.2 htail p

def x (a b : Bool) : Bool := Bool.xor a b

theorem dirty_cubic (a b c r : Bool) :
    x (r && c) ((x r (a && b)) && c) = (a && b && c) := by
  cases a <;> cases b <;> cases c <;> cases r <;> decide

theorem erase_phase (m q f : Bool) (h : q = f) :
    x (m && q) (m && f) = false := by
  subst q
  cases m <;> cases f <;> decide

theorem cofactor_join (s f0 f1 : Bool) :
    (if s then f1 else f0) = x f0 (s && x f0 f1) := by
  cases s <;> cases f0 <;> cases f1 <;> decide

theorem polarized_shift (a b da db : Bool) :
    x (x a da && x b db) (a && b) =
      x (x (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem abel_step (p c m d z : Bool) :
    x (p && c) (x (m && x c d) z) =
      x (x p m && c) (x (m && d) z) := by
  cases p <;> cases c <;> cases m <;> cases d <;> cases z <;> decide

theorem paid_twice_units :
    2 * 256 - (2 * 153 + 1) = 205 ∧ 37 + 23 = 60 := by decide

end GVQCC.V45
