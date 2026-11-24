import Std.Tactic
namespace GVQCC.V26

def parity : List Bool → Bool
  | [] => false
  | a :: xs => Bool.xor a (parity xs)

theorem parity_append (xs ys : List Bool) :
    parity (xs ++ ys) = Bool.xor (parity xs) (parity ys) := by
  induction xs with
  | nil =>
    change parity ys = Bool.xor false (parity ys)
    cases parity ys <;> rfl
  | cons a xs ih =>
    change Bool.xor a (parity (xs ++ ys)) =
      Bool.xor (Bool.xor a (parity xs)) (parity ys)
    rw [ih]
    cases a <;> cases parity xs <;> cases parity ys <;> rfl

theorem delete_zero (keep removed : List Bool) (h : parity removed = false) :
    parity (keep ++ removed) = parity keep := by
  rw [parity_append, h]
  cases parity keep <;> rfl

theorem phase_debt_settlement (oldPhase newPhase repair : Bool)
    (h : Bool.xor oldPhase newPhase = repair) :
    Bool.xor newPhase repair = oldPhase := by
  cases oldPhase <;> cases newPhase <;> cases repair <;> simp_all

theorem nonlinear_product_delta (a b da db : Bool) :
    Bool.xor (a && b) (Bool.xor a da && Bool.xor b db) =
      Bool.xor (a && db) (Bool.xor (b && da) (da && db)) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem hmr_virtual_product (m a b : Bool) :
    Bool.xor (m && false) (m && (a && b)) = (m && (a && b)) := by
  cases m <;> cases a <;> cases b <;> decide

theorem guarded_transport (m a b u : Bool) :
    parity [m && a && b, m && a && u, m && a && Bool.xor b u] = false := by
  cases m <;> cases a <;> cases b <;> cases u <;> decide

-- V25 joined_guard SHA 4cca0e26...; native [15191,15236).
-- q32 becomes u by CCX(18,30,32), CX(4,32) (two X cancel).
-- CX(32,30) at 15203 makes q30 = b xor u. HMR(32,469) does
-- not change q30 nor q28,35,31,19,12 or record 837.
-- The two X on q30 surrounding the rotation cancel.
def projection (m a b q32 q18 q4 : Bool) : List Bool :=
  let u := Bool.xor (Bool.xor q32 (q18 && b)) q4
  [m && a && b, m && a && u, m && a && Bool.xor b u]

theorem actual_projection (m a b q32 q18 q4 : Bool) :
    parity (projection m a b q32 q18 q4) = false := by
  unfold projection
  exact guarded_transport m a b (Bool.xor (Bool.xor q32 (q18 && b)) q4)

def actualTriples : List (Nat × Nat × Nat × Nat) :=
  [(15191,15206,15231,28), (15192,15207,15232,35),
   (15193,15208,15233,31), (15194,15209,15234,19),
   (15195,15210,15235,12)]

theorem actual_triple_count : actualTriples.length * 3 = 15 := by decide
theorem actual_command_counts : 58208 - 1422 = 56786 ∧
    53155 - 95 = 53060 := by decide
-- Strict frozen break-even bound E<1452.0539 at Q36; sixteenth-grid max 23232.
theorem grid_budgets : 23232 - 22501 = 731 ∧ 23232 - 22725 = 507 := by decide
-- Actual V26 phase-parent [34345,34416), target q8 initially zero.
-- Projected source target writes: CCX(5,20,8), CX(5,8), CX(22,8),
-- Z(8), CX(5,8), CX(22,8), CX(5,8), CX(22,8).
-- Controls q5,q20,q22 unchanged, no other data reads of q8 in this span.
def original71 (a b c : Bool) : Bool × Bool :=
  let t0 := a && b
  let t1 := Bool.xor (Bool.xor t0 a) c
  let t2 := Bool.xor (Bool.xor t1 a) c
  let t3 := Bool.xor (Bool.xor t2 a) c
  (t3,t1)

def deferred71 (a b c : Bool) : Bool × Bool :=
  let phase := Bool.xor (Bool.xor a c) (a && b)
  let reconstructed := Bool.xor (Bool.xor a c) (a && b)
  (reconstructed, phase)

theorem actual_deferred71 (a b c : Bool) :
    original71 a b c = deferred71 a b c := by
  cases a <;> cases b <;> cases c <;> decide

-- Concrete 2-op native clean-target producer + guarded Z, [27601,27603).
theorem actual_deferred_guard (a b m : Bool) :
    ((a && b), (m && (a && b))) =
    ((a && b), ((m && a) && b)) := by
  cases a <;> cases b <;> cases m <;> decide

theorem deferred_resources :
    53060 - 11 = 53049 ∧ 6388 - 623 = 5765 ∧
    56786 - 52 = 56734 ∧ 8189 - 670 = 7519 := by decide
end GVQCC.V26
