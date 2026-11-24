import Std.Tactic
namespace GVQCC.V35

def runUpdate : Bool → List Bool → Bool
  | q, [] => q
  | q, f :: fs => runUpdate (Bool.xor q f) fs

def phaseUpdates (m : Bool) : List Bool → Bool
  | [] => false
  | f :: fs => Bool.xor (m && f) (phaseUpdates m fs)

theorem measured_telescope (m q : Bool) (fs : List Bool) :
    (m && runUpdate q fs) = Bool.xor (m && q) (phaseUpdates m fs) := by
  induction fs generalizing q with
  | nil =>
    cases m <;> cases q <;> rfl
  | cons f fs ih =>
    change (m && runUpdate (Bool.xor q f) fs) =
      Bool.xor (m && q) (Bool.xor (m && f) (phaseUpdates m fs))
    rw [ih]
    cases h : phaseUpdates m fs <;> cases m <;> cases q <;> cases f <;> rfl

theorem step_debt (m q f : Bool) :
    Bool.xor (m && q) (m && Bool.xor q f) = (m && f) := by
  cases m <;> cases q <;> cases f <;> decide

theorem guarded_step (m q f g : Bool) :
    Bool.xor (m && q) (m && Bool.xor q (g && f)) = (g && m && f) := by
  cases m <;> cases q <;> cases f <;> cases g <;> decide

theorem pair_hmr (a b m : Bool) :
    Bool.xor (m && Bool.xor a b) (m && b) = (m && a) := by
  cases a <;> cases b <;> cases m <;> decide

theorem packed_update (a b f : Bool) :
    Bool.xor (Bool.xor a f) b = Bool.xor (Bool.xor a b) f := by
  cases a <;> cases b <;> cases f <;> decide

theorem carry_exchange (a b c : Bool) :
    Bool.xor (a && b) c =
      Bool.xor (Bool.xor a c && b) (c && !b) := by
  cases a <;> cases b <;> cases c <;> decide

theorem polar_transport (a b da db : Bool) :
    Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
      Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem resource_bookkeeping :
    4576 - 399 = 4177 ∧ 3809 - 107 = 3702 ∧
    4869 - 110 = 4759 ∧ 3702 - 21 = 3681 ∧
    23077 + 9 * 16 = 23221 := by decide

end GVQCC.V35
