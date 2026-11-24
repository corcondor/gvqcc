import Std.Tactic
namespace GVQCC.V36
def x (a b : Bool) : Bool := Bool.xor a b

-- Observable substitution, no need to recover the virtual coordinate itself.
theorem guarded_observation (g f h t : Bool) (eq : (g && f) = (g && h)) :
    x t (g && f) = x t (g && h) := by rw [eq]

theorem switch_coordinate (a b h : Bool) (rel : a = x b h) :
    x b h = a := by exact rel.symm

-- Shared AND distributed to multiple targets using a reversible affine fanout.
theorem shared_product (a b u v : Bool) :
    x (x v u) (x u (a && b)) = x v (a && b) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide

-- Dirty helper realizes a cubic target update without an additional line.
theorem dirty_cubic (a b c h t : Bool) :
    x (x t (x h (a && b) && c)) (h && c) = x t (a && b && c) := by
  cases a <;> cases b <;> cases c <;> cases h <;> cases t <;> decide

-- Measurement phase derivative. If the complete relative phase is independent
-- of the outcome, the oracle phase equals either specialization.
theorem outcome_specialization (p : Bool → Bool)
    (h : x (p false) (p true) = false) (m : Bool) :
    p m = p false := by
  cases m
  · rfl
  · cases h0 : p false <;> cases h1 : p true <;> simp_all [x, Bool.xor]

def parity : List Bool → Bool
  | [] => false
  | b :: bs => x b (parity bs)

theorem parity_map_derivative (fs : List (Bool → Bool)) :
    x (parity (fs.map (fun f => f false))) (parity (fs.map (fun f => f true))) =
    parity (fs.map (fun f => x (f false) (f true))) := by
  induction fs with
  | nil => rfl
  | cons f fs ih =>
    simp only [List.map_cons, parity]
    rw [← ih]
    cases a : f false <;> cases b : f true <;>
      cases c : parity (fs.map (fun f => f false)) <;>
      cases d : parity (fs.map (fun f => f true)) <;> decide

theorem carry_selector (a b c : Bool) :
    x (a && b) c = x (x a c && b) (c && !b) := by
  cases a <;> cases b <;> cases c <;> decide

end GVQCC.V36
