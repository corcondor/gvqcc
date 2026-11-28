import Std

namespace ObserverPhase

def parity : List Bool → Bool
  | [] => false
  | x :: xs => Bool.xor x (parity xs)

theorem gate_parity (c : Bool) (xs : List Bool) :
    (c && parity xs) = parity (xs.map (fun x => c && x)) := by
  induction xs with
  | nil => cases c <;> decide
  | cons x xs ih =>
      cases c
      · simp [parity, ← ih]
      · simp [parity, ← ih]

theorem guarded_ccz (g c a b : Bool) (xs : List Bool)
    (h : g = true → c = true → (a && b) = parity xs) :
    (g && c && a && b) = (g && parity (xs.map (fun x => c && x))) := by
  rw [← gate_parity c xs]
  cases g <;> cases c <;> cases a <;> cases b <;> simp_all

#print axioms gate_parity
#print axioms guarded_ccz
end ObserverPhase
