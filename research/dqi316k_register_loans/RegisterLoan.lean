import Init
namespace GVQCC.RegisterLoan

/-- Clear the lender using a reconstructible Boolean value f, then
    transfer the borrower by two CNOTs. No initialized extra qubit. -/
def openLoan (f lender borrower : Bool) : Bool × Bool :=
  let t := Bool.xor lender f
  let u := Bool.xor t borrower
  (u, Bool.xor borrower u)

/-- Inverse CNOT pair and reconstruction of the lender. -/
def closeLoan (f occupied spare : Bool) : Bool × Bool :=
  let v := Bool.xor spare occupied
  let t := Bool.xor occupied v
  (Bool.xor t f, v)

theorem roundtrip (f lender borrower : Bool) :
    closeLoan f (openLoan f lender borrower).1 (openLoan f lender borrower).2 =
      (lender, borrower) := by
  cases f <;> cases lender <;> cases borrower <;> decide

theorem open_clean (f borrower : Bool) :
    openLoan f f borrower = (borrower, false) := by
  cases f <;> cases borrower <;> decide

theorem close_clean (f borrower : Bool) :
    closeLoan f borrower false = (f, borrower) := by
  cases f <;> cases borrower <;> decide

/-- Arbitrary borrower computation while lender reconstruction is available. -/
theorem arbitrary_update (f b : Bool) (g : Bool → Bool) :
    closeLoan f (g (openLoan f f b).1) (openLoan f f b).2 =
      (f, g b) := by
  rw [open_clean]
  exact close_clean f (g b)

/-- The side data can change, provided its reconstruction function is stable. -/
theorem stable_reconstruction {A : Type} (f : A → Bool)
    (s t : A) (h : f s = f t) (b : Bool) (g : Bool → Bool) :
    closeLoan (f t) (g (openLoan (f s) (f s) b).1)
      (openLoan (f s) (f s) b).2 = (f s, g b) := by
  rw [← h]
  exact arbitrary_update (f s) b g

theorem control_relabel (f b a c : Bool) :
    Bool.xor c (a && (openLoan f f b).1) = Bool.xor c (a && b) := by
  rw [open_clean]

theorem target_relabel (f b a c : Bool) :
    closeLoan f (Bool.xor (openLoan f f b).1 (a && c))
      (openLoan f f b).2 = (f, Bool.xor b (a && c)) := by
  exact arbitrary_update f b (fun x => Bool.xor x (a && c))

/-- HMR phase for the relocated logical value: every outcome m. -/
theorem phase_relabel (f b m p : Bool) :
    Bool.xor p (m && (openLoan f f b).1) = Bool.xor p (m && b) := by
  rw [open_clean]

/-- Two simultaneous disjoint leases remain exact even when both borrowed
    values have changed, provided both original reconstruction values exist. -/
theorem concurrent_close (f g x y : Bool) :
    (closeLoan f x false, closeLoan g y false) = ((f,x),(g,y)) := by
  rw [close_clean, close_clean]

end GVQCC.RegisterLoan
#print axioms GVQCC.RegisterLoan.roundtrip
#print axioms GVQCC.RegisterLoan.open_clean
#print axioms GVQCC.RegisterLoan.close_clean
#print axioms GVQCC.RegisterLoan.arbitrary_update
#print axioms GVQCC.RegisterLoan.stable_reconstruction
#print axioms GVQCC.RegisterLoan.control_relabel
#print axioms GVQCC.RegisterLoan.target_relabel
#print axioms GVQCC.RegisterLoan.phase_relabel
#print axioms GVQCC.RegisterLoan.concurrent_close
