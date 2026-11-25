import Std.Tactic
namespace GVQCC.V42
def X := Bool.xor

-- Basis shear on the selector-feature tensor: all Boolean values,
-- not a numerical low-rank approximation.
theorem tensorShear (a b l m : Bool) :
    X (a && l) (b && m) =
    X ((X a b) && l) (b && X l m) := by
  cases a <;> cases b <;> cases l <;> cases m <;> decide

theorem cofactorTensor (a b l00 l01 l10 l11 : Bool) :
    (if a then if b then l11 else l10 else if b then l01 else l00) =
      X (X l00 (a && X l00 l10))
        (X (b && X l00 l01) (a && b && X (X l00 l01) (X l10 l11))) := by
  cases a <;> cases b <;> cases l00 <;> cases l01 <;>
  cases l10 <;> cases l11 <;> decide

-- Gauge choice: the departure coordinate can be absorbed with the
-- incoming product. Equality is conditional on the reachable relation.
theorem gauge (r h p c : Bool) (hc : X h p = c) :
    X (X r h) p = X r c := by
  cases r <;> cases h <;> cases p <;> cases c <;> simp_all [X]

theorem shearInvolution (r p : Bool) : X (X r p) p = r := by
  cases r <;> cases p <;> decide

-- Transport a masked equality through simultaneous updates, retaining
-- the mixed term. All additions are in GF(2).
theorem maskedTransport (a f g s d e : Bool) :
    (X a s && X (X f d) (X g e)) =
      X (X (a && X f g) (a && X d e))
        (X (s && X f g) (s && X d e)) := by
  cases a <;> cases f <;> cases g <;> cases s <;>
  cases d <;> cases e <;> decide

theorem phaseTransport (m r h p : Bool) :
    X (m && r) (m && X (X r h) p) =
      (m && X h p) := by
  cases m <;> cases r <;> cases h <;> cases p <;> decide

theorem conditionalCarrier (a b c r t : Bool) (hz : (c && r) = false) :
    (X (X r (a && b)) (a && b), X t (c && X r (a && b))) =
      (r, X t (a && b && c)) := by
  cases a <;> cases b <;> cases c <;> cases r <;> cases t <;> simp_all [X]

theorem receipts : 3211 - 56 = 3155 ∧
    3211 - 68 = 3143 ∧ 23127 + 96 = 23223 ∧ 1494*16+7=23911 := by decide
end GVQCC.V42
