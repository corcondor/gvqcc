import Std

namespace GVQCCProgram

/- A new whole-program contract: no prescribed cache basis, number of
   intermediates, cut, nonlinear coordinates, or measurement transcript length.
   The very same gate list determines semantics and paid count. -/

structure Algebra (α : Type) where
  zero : α
  one : α
  add : α → α → α
  mul : α → α → α

def scalar : Algebra Bool := ⟨false, true, Bool.xor, Bool.and⟩
def packed (full : Nat) : Algebra Nat :=
  ⟨0, full, fun a b => a ^^^ b, fun a b => a &&& b⟩

structure Morph {α β : Type} (A : Algebra α) (B : Algebra β)
    (f : α → β) : Prop where
  zero : f A.zero = B.zero
  one : f A.one = B.one
  add : ∀ x y, f (A.add x y) = B.add (f x) (f y)
  mul : ∀ x y, f (A.mul x y) = B.mul (f x) (f y)

theorem rowMorph (full i : Nat) (h : full.testBit i = true) :
    Morph (packed full) scalar (fun x => x.testBit i) := by
  constructor
  · simp [packed, scalar]
  · exact h
  · intro x y
    simp [packed, scalar, Nat.testBit_xor]
  · intro x y
    simp [packed, scalar]

def rd {α : Type} (z : α) : List α → Nat → α
  | [], _ => z
  | x :: _, 0 => x
  | _ :: xs, n+1 => rd z xs n

def wr {α : Type} : List α → Nat → α → List α
  | [], _, _ => []
  | _ :: xs, 0, v => v :: xs
  | x :: xs, n+1, v => x :: wr xs n v

theorem rd_map {α β : Type} (f : α → β) (z : α)
    (xs : List α) (i : Nat) :
    rd (f z) (xs.map f) i = f (rd z xs i) := by
  induction xs generalizing i with
  | nil => rfl
  | cons x xs ih =>
    cases i with
    | zero => rfl
    | succ i => simpa [rd] using ih i

theorem wr_map {α β : Type} (f : α → β) (xs : List α) (i : Nat) (v : α) :
    (wr xs i v).map f = wr (xs.map f) i (f v) := by
  induction xs generalizing i with
  | nil => rfl
  | cons x xs ih =>
    cases i with
    | zero => rfl
    | succ i => simp [wr, ih]

theorem rd_morph {α β : Type} {A : Algebra α} {B : Algebra β}
    {f : α → β} (h : Morph A B f) (xs : List α) (i : Nat) :
    f (rd A.zero xs i) = rd B.zero (xs.map f) i := by
  rw [← h.zero, rd_map]

def addAt {α : Type} (A : Algebra α) (xs : List α) (i : Nat) (v : α) :=
  wr xs i (A.add (rd A.zero xs i) v)

theorem addAt_map {α β : Type} {A : Algebra α} {B : Algebra β}
    {f : α → β} (h : Morph A B f) (xs : List α) (i : Nat) (v : α) :
    (addAt A xs i v).map f = addAt B (xs.map f) i (f v) := by
  simp only [addAt, wr_map, h.add, rd_morph h]

/- Arbitrary nonlinear expressions used in coordinate encodings. The
   search may choose different expression DAGs and different frames at
   every stage. This is not limited to the old 98-dimensional cut. -/
inductive Expr where
  | zero
  | one
  | wire (i : Nat)
  | xor (a b : Expr)
  | and (a b : Expr)
  deriving Repr

def evalExpr {α : Type} (A : Algebra α) (q : List α) : Expr → α
  | .zero => A.zero
  | .one => A.one
  | .wire i => rd A.zero q i
  | .xor a b => A.add (evalExpr A q a) (evalExpr A q b)
  | .and a b => A.mul (evalExpr A q a) (evalExpr A q b)

theorem expr_map {α β : Type} {A : Algebra α} {B : Algebra β}
    {f : α → β} (h : Morph A B f) (q : List α) (e : Expr) :
    f (evalExpr A q e) = evalExpr B (q.map f) e := by
  induction e with
  | zero => exact h.zero
  | one => exact h.one
  | wire i =>
    exact rd_morph h q i
  | xor a b ia ib => simp [evalExpr, h.add, ia, ib]
  | and a b ia ib => simp [evalExpr, h.mul, ia, ib]

def encode {α : Type} (A : Algebra α) (q : List α) (frame : List Expr) :=
  frame.map (evalExpr A q)

theorem frame_map {α β : Type} {A : Algebra α} {B : Algebra β}
    {f : α → β} (h : Morph A B f) (q : List α) (frame : List Expr) :
    (encode A q frame).map f = encode B (q.map f) frame := by
  induction frame with
  | nil => rfl
  | cons e es ih =>
    simp only [encode, List.map_cons] at ih ⊢
    rw [expr_map h, ih]

inductive Gate where
  | x (t : Nat)
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  | hmr (t event : Nat)
  | z (t : Nat)
  | cz (a b : Nat)
  | zIf (t event : Nat)
  | czIf (a b event : Nat)
  deriving Repr

structure State (α : Type) where
  q : List α
  constantPhase : α
  eventPhase : List α
  deriving Repr, DecidableEq

def project {α β : Type} (f : α → β) (s : State α) : State β :=
  ⟨s.q.map f, f s.constantPhase, s.eventPhase.map f⟩

/- HMR is represented by a fresh independent event coefficient.
   Reset uses the PRE-measurement value. No conditional data gates are
   accepted by this language. The native exporter must check that scope. -/
def step {α : Type} (A : Algebra α) (g : Gate) (s : State α) : State α :=
  let wireVal := rd A.zero s.q
  match g with
  | .x t => {s with q := addAt A s.q t A.one}
  | .cx a t => {s with q := addAt A s.q t (wireVal a)}
  | .ccx a b t => {s with q := addAt A s.q t (A.mul (wireVal a) (wireVal b))}
  | .hmr t j => {s with q := wr s.q t A.zero,
                       eventPhase := addAt A s.eventPhase j (wireVal t)}
  | .z t => {s with constantPhase := A.add s.constantPhase (wireVal t)}
  | .cz a b => {s with constantPhase := A.add s.constantPhase (A.mul (wireVal a) (wireVal b))}
  | .zIf t j => {s with eventPhase := addAt A s.eventPhase j (wireVal t)}
  | .czIf a b j => {s with eventPhase := addAt A s.eventPhase j (A.mul (wireVal a) (wireVal b))}

theorem step_map {α β : Type} {A : Algebra α} {B : Algebra β}
    {f : α → β} (h : Morph A B f) (g : Gate) (s : State α) :
    project f (step A g s) = step B g (project f s) := by
  cases s with
  | mk q c p =>
    cases g <;>
      simp [step, project, addAt_map h, wr_map, h.zero, h.one, h.add, h.mul,
        rd_morph h]

def run {α : Type} (A : Algebra α) : List Gate → State α → State α
  | [], s => s
  | g :: gs, s => run A gs (step A g s)

theorem run_map {α β : Type} {A : Algebra α} {B : Algebra β}
    {f : α → β} (h : Morph A B f) (gs : List Gate) (s : State α) :
    project f (run A gs s) = run B gs (project f s) := by
  induction gs generalizing s with
  | nil => rfl
  | cons g gs ih =>
    simp only [run]
    rw [ih, step_map h]

theorem run_append {α : Type} (A : Algebra α) (p q : List Gate) (s : State α) :
    run A (p ++ q) s = run A q (run A p s) := by
  induction p generalizing s with
  | nil => rfl
  | cons g gs ih => simpa [run] using ih (step A g s)

/- Arbitrary encoded boundaries, including changed cache cardinality and
   nonzero carried scratch/phase in the interior. Only the final ABI is clean. -/
theorem join_stages {α : Type} (A : Algebra α) (p q : List Gate)
    (s mid out : State α) (hp : run A p s = mid) (hq : run A q mid = out) :
    run A (p ++ q) s = out := by
  rw [run_append, hp, hq]

def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs

theorem paid_append (p q : List Gate) : paid (p ++ q) = paid p + paid q := by
  induction p with
  | nil => simp [paid]
  | cons g gs ih => cases g <;> simp [paid, ih, Nat.add_assoc]

def validGate (n next : Nat) : Gate → Bool
  | .x t | .z t => decide (t < n)
  | .cx a t | .cz a t => decide (a < n) && decide (t < n) && a != t
  | .ccx a b t => decide (a < n) && decide (b < n) && decide (t < n) && a != b && a != t && b != t
  | .hmr t j => decide (t < n) && j == next
  | .zIf t j => decide (t < n) && decide (j < next)
  | .czIf a b j => decide (a < n) && decide (b < n) && a != b && decide (j < next)

def events : List Gate → Nat
  | [] => 0
  | .hmr _ _ :: gs => 1 + events gs
  | _ :: gs => events gs

def wellFormedFrom (n next : Nat) : List Gate → Bool
  | [] => true
  | g :: gs =>
    validGate n next g &&
      wellFormedFrom n (next + (match g with | .hmr _ _ => 1 | _ => 0)) gs

def startState (q : List Nat) (k : Nat) : State Nat := ⟨q, 0, List.replicate k 0⟩

/- The budget, width, executable program, forward/backward legal truth
   masks and cleanup condition are connected in ONE proposition. -/
def Accepted (n full budget : Nat) (initial target : List Nat) (gs : List Gate) : Prop :=
  n ≤ 128 ∧ initial.length = n ∧ target.length = n ∧
  wellFormedFrom n 0 gs = true ∧ paid gs ≤ budget ∧
  run (packed full) gs (startState initial (events gs)) =
    startState target (events gs)

instance acceptedDecidable (n full budget : Nat) (initial target : List Nat) (gs : List Gate) :
    Decidable (Accepted n full budget initial target gs) := by
  unfold Accepted
  infer_instance

def check (n full budget : Nat) (initial target : List Nat) (gs : List Gate) : Bool :=
  decide (Accepted n full budget initial target gs)

theorem check_sound (n full budget : Nat) (initial target : List Nat) (gs : List Gate)
    (h : check n full budget initial target gs = true) :
    Accepted n full budget initial target gs := by
  exact of_decide_eq_true h

def phaseParity (m : Nat → Bool) (j : Nat) : List Bool → Bool
  | [] => false
  | x :: xs => Bool.xor (Bool.and x (m j)) (phaseParity m (j+1) xs)

def branchPhase (m : Nat → Bool) (s : State Bool) : Bool :=
  Bool.xor s.constantPhase (phaseParity m 0 s.eventPhase)

theorem parity_zero (m : Nat → Bool) (j k : Nat) :
    phaseParity m j (List.replicate k false) = false := by
  induction k generalizing j with
  | zero => rfl
  | succ k ih => simp [List.replicate, phaseParity, ih]

theorem project_start (row k : Nat) (q : List Nat) :
    project (fun x => x.testBit row) (startState q k) =
      (⟨q.map (fun x => x.testBit row), false, List.replicate k false⟩ : State Bool) := by
  simp [project, startState, List.map_replicate]

/- Main transfer theorem: a proof about the actual packed circuit implies
   every individual legal row and every independent HMR outcome vector.
   The native decoder and external quantum/KickMix semantics are separate. -/
theorem all_branches (n full budget row : Nat) (initial target : List Nat)
    (gs : List Gate) (hrow : full.testBit row = true)
    (h : Accepted n full budget initial target gs) (m : Nat → Bool) :
    let s := run scalar gs
      (⟨initial.map (fun x => x.testBit row), false, List.replicate (events gs) false⟩ : State Bool)
    s.q = target.map (fun x => x.testBit row) ∧ branchPhase m s = false := by
  have hrun := h.2.2.2.2.2
  have hproj := congrArg (project (fun x : Nat => x.testBit row)) hrun
  simp only [run_map (rowMorph full row hrow), project_start] at hproj
  dsimp
  rw [hproj]
  simp [branchPhase, parity_zero]

/- Regression fixture ONLY: a nonlocal shared product, reused outputs,
   and HMR cleanup; its cost certificate concerns this five-wire fixture,
   not any GVQCC candidate. -/
def fixture : List Gate :=
  [.ccx 0 1 4, .cx 4 2, .cx 4 3, .hmr 4 0, .czIf 0 1 0]

-- 4 addresses, output q2/q3 initially zero, scratch q4 initially zero.
example : Accepted 5 15 1 [10,12,0,0,0] [10,12,8,8,0] fixture := by
  decide

-- Deleting the measurement correction must fail.
example : ¬ Accepted 5 15 1 [10,12,0,0,0] [10,12,8,8,0]
    [.ccx 0 1 4, .cx 4 2, .cx 4 3, .hmr 4 0] := by
  decide

end GVQCCProgram
