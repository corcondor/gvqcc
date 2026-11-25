import Std
namespace V54
def bval (b : Bool) : Int := if b then 1 else 0

-- Difference of two observations replaces explicit storage of a product.
theorem signed_toggle (b f : Bool) :
    bval (Bool.xor b f) - bval b = bval f * (1 - 2*bval b) := by
  cases b <;> cases f <;> decide

theorem shared_toggle (b f g : Bool) :
    Bool.xor (Bool.xor b f) (Bool.xor f g) = Bool.xor b g := by
  cases b <;> cases f <;> cases g <;> decide

theorem singleton_pair (a b c : Bool) :
    Bool.xor (Bool.xor a b) (Bool.xor b c) = Bool.xor a c := by
  cases a <;> cases b <;> cases c <;> decide

-- L legal, u illegal, 2*h total. A direct balanced extension exists
-- if c ones on the legal set can be padded to h.
theorem padding_count (c h u : Nat) (hc : c ≤ h) (hu : h ≤ c+u) :
    ∃ d : Nat, d ≤ u ∧ c+d=h := by
  exact ⟨h-c, by omega, by omega⟩

-- When L <= 3/4 of the cube, every support count is either directly
-- balanceable, sparse enough for a signed pair, or has sparse complement.
theorem support_cases (L u h c : Nat) (ht : L+u=2*h)
    (hl : 2*L ≤ 3*h) (hc : c ≤ L) :
    (c ≤ h ∧ h ≤ c+u) ∨ c ≤ u ∨ L-c ≤ u := by
  omega

-- Dense support can instead be split into two directly balanceable sets.
theorem dense_split (L u h c : Nat) (ht : L+u=2*h)
    (hl : 2*L ≤ 3*h) (hc : c ≤ L) (hd : h < c) :
    c/2 ≤ h ∧ h ≤ c/2+u ∧ c-c/2 ≤ h ∧ h ≤ c-c/2+u := by
  omega

theorem complement_is_illegal (x : Nat) (hx : 1 ≤ x)
    (hs : x ≤ 1060850) :
    3133452 < 4194303-x := by
  omega

theorem actual_domain : 2*3133452 ≤ 3*2097152 := by decide

-- The ten negative observations all have the same pivot, so one
-- dyadic rotation replaces all their negative angles modulo one turn.
theorem merged_negative :
    (2^34 : Nat) - (2^24+2^25+2^26+2^27+2^28+2^29+
      2^30+2^31+2^32+2^33) = 2^24 := by decide
end V54
