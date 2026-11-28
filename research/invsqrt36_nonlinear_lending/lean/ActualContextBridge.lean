import Std.Tactic.BVDecide

/-! Concrete original and emitted instruction lists for the seven V4 bridge
substitutions. Inspired by PR #28 ActualCarry.lean in this repository.
Source SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03.
Emitted full hybrid SHA256 ca39e8c1bf363dd0909b37c4bc34f7f2aaad2926989469e3bd4399f041ff114d.
The removed outcome is normalized to zero, with global phase/rotation
independence and downstream phase-only-use independently verified by the
whole-program BDD model. This proof is NOT an arbitrary-outcome HMR proof.
At entry q36=0; exit q35 is omitted and q36 occupies physical q35.
One local event is represented by a Bool; its original ID is retained in the list.
-/
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.ActualContextBridge
inductive Gate where
  | x (t : Nat)
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  | swap (a b : Nat)
  | hmr0 (q eventId : Nat)
  | clearEvent (eventId : Nat)
  deriving DecidableEq, Repr

private def bit (s : BitVec 37) (i : Nat) : BitVec 37 := (s >>> i) &&& 1
private def toggle (s : BitVec 37) (i : Nat) (v : BitVec 37) : BitVec 37 :=
  s ^^^ ((v &&& 1) <<< i)
private def clear (s : BitVec 37) (i : Nat) : BitVec 37 :=
  s &&& ~~~((1 : BitVec 37) <<< i)

private def step (r : BitVec 37 × Bool × Bool) : Gate → BitVec 37 × Bool × Bool
  | .x t => (toggle r.1 t 1,r.2)
  | .cx a t => (toggle r.1 t (bit r.1 a),r.2)
  | .ccx a b t => (toggle r.1 t (bit r.1 a &&& bit r.1 b),r.2)
  | .swap a b =>
    let v := bit r.1 a ^^^ bit r.1 b
    (toggle (toggle r.1 a v) b v,r.2)
  | .hmr0 q _ => (clear r.1 q,r.2.1,false)
  | .clearEvent _ => (r.1,r.2.1,false)

private def run (g : List Gate) (r : BitVec 37 × Bool × Bool) := g.foldl step r
private def lift (r : BitVec 37 × Bool × Bool) : BitVec 37 × Bool × Bool :=
  (toggle (clear (clear r.1 35) 36) 36 (bit r.1 35),r.2)

private def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs

private def wireOK (n : Nat) : Gate → Bool
  | .x t | .hmr0 t _ => decide (t < n)
  | .cx a t | .swap a t => decide (a < n ∧ t < n ∧ a ≠ t)
  | .ccx a b t => decide (a < n ∧ b < n ∧ t < n ∧ a ≠ b ∧ a ≠ t ∧ b ≠ t)
  | .clearEvent _ => true

private def src7754 : List Gate := [.cx 35 15, .cx 35 33, .ccx 15 33 36, .cx 35 36, .cx 35 15, .cx 15 33, .hmr0 35 513]
private def dst7754 : List Gate := [.cx 33 35, .cx 14 11, .cx 27 11, .cx 14 12, .cx 27 12, .ccx 11 12 15, .cx 27 12, .cx 14 12, .cx 27 11, .cx 14 11, .x 15, .cx 12 15, .cx 27 15, .ccx 35 15 33, .cx 27 15, .cx 12 15, .x 15, .cx 14 11, .cx 27 11, .cx 14 12, .cx 27 12, .ccx 11 12 15, .cx 27 12, .cx 14 12, .cx 27 11, .cx 14 11, .cx 15 35, .swap 33 35, .clearEvent 513]
private def ctx7754 (s : BitVec 37) : BitVec 37 := (1 : BitVec 37) ^^^ (bit s 12) ^^^ (bit s 14) ^^^ (bit s 11 &&& bit s 12) ^^^ (bit s 11 &&& bit s 14) ^^^ (bit s 11 &&& bit s 27) ^^^ (bit s 12 &&& bit s 14) ^^^ (bit s 12 &&& bit s 27)

theorem concrete_7754 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 33 ^^^ bit s 35) &&& (ctx7754 s ^^^ bit s 33) = 0) :
    run src7754 (s,phase,event) = lift (run dst7754 (s,phase,event)) := by
  apply Prod.ext
  · unfold src7754 dst7754 ctx7754 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_7754 :
    src7754.all (wireOK 37) = true ∧ dst7754.all (wireOK 36) = true ∧
    paid src7754 = 1 ∧ paid dst7754 = 3 := by decide


private def src7912 : List Gate := [.cx 35 15, .cx 35 12, .ccx 15 12 36, .cx 35 36, .cx 35 15, .cx 15 12, .hmr0 35 522]
private def dst7912 : List Gate := [.cx 12 35, .cx 14 10, .cx 27 10, .cx 14 11, .cx 27 11, .ccx 10 11 15, .cx 27 11, .cx 14 11, .cx 27 10, .cx 14 10, .x 15, .cx 11 15, .cx 27 15, .ccx 35 15 12, .cx 27 15, .cx 11 15, .x 15, .cx 14 10, .cx 27 10, .cx 14 11, .cx 27 11, .ccx 10 11 15, .cx 27 11, .cx 14 11, .cx 27 10, .cx 14 10, .cx 15 35, .swap 12 35, .clearEvent 522]
private def ctx7912 (s : BitVec 37) : BitVec 37 := (1 : BitVec 37) ^^^ (bit s 11) ^^^ (bit s 14) ^^^ (bit s 10 &&& bit s 11) ^^^ (bit s 10 &&& bit s 14) ^^^ (bit s 10 &&& bit s 27) ^^^ (bit s 11 &&& bit s 14) ^^^ (bit s 11 &&& bit s 27)

theorem concrete_7912 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 12 ^^^ bit s 35) &&& (ctx7912 s ^^^ bit s 12) = 0) :
    run src7912 (s,phase,event) = lift (run dst7912 (s,phase,event)) := by
  apply Prod.ext
  · unfold src7912 dst7912 ctx7912 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_7912 :
    src7912.all (wireOK 37) = true ∧ dst7912.all (wireOK 36) = true ∧
    paid src7912 = 1 ∧ paid dst7912 = 3 := by decide


private def src8096 : List Gate := [.cx 35 15, .cx 35 11, .ccx 15 11 36, .cx 35 36, .cx 35 15, .cx 15 11, .hmr0 35 532]
private def dst8096 : List Gate := [.cx 11 35, .cx 14 9, .cx 27 9, .cx 14 10, .cx 27 10, .ccx 9 10 15, .cx 27 10, .cx 14 10, .cx 27 9, .cx 14 9, .x 15, .cx 10 15, .cx 27 15, .ccx 35 15 11, .cx 27 15, .cx 10 15, .x 15, .cx 14 9, .cx 27 9, .cx 14 10, .cx 27 10, .ccx 9 10 15, .cx 27 10, .cx 14 10, .cx 27 9, .cx 14 9, .cx 15 35, .swap 11 35, .clearEvent 532]
private def ctx8096 (s : BitVec 37) : BitVec 37 := (1 : BitVec 37) ^^^ (bit s 10) ^^^ (bit s 14) ^^^ (bit s 9 &&& bit s 10) ^^^ (bit s 9 &&& bit s 14) ^^^ (bit s 9 &&& bit s 27) ^^^ (bit s 10 &&& bit s 14) ^^^ (bit s 10 &&& bit s 27)

theorem concrete_8096 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 11 ^^^ bit s 35) &&& (ctx8096 s ^^^ bit s 11) = 0) :
    run src8096 (s,phase,event) = lift (run dst8096 (s,phase,event)) := by
  apply Prod.ext
  · unfold src8096 dst8096 ctx8096 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_8096 :
    src8096.all (wireOK 37) = true ∧ dst8096.all (wireOK 36) = true ∧
    paid src8096 = 1 ∧ paid dst8096 = 3 := by decide


private def src9735 : List Gate := [.cx 35 15, .cx 35 29, .ccx 15 29 36, .cx 35 36, .cx 35 15, .cx 15 29, .hmr0 35 655]
private def dst9735 : List Gate := [.cx 29 35, .cx 14 6, .ccx 6 27 15, .cx 14 6, .cx 6 15, .cx 27 15, .ccx 35 15 29, .cx 27 15, .cx 6 15, .cx 14 6, .ccx 6 27 15, .cx 14 6, .cx 15 35, .swap 29 35, .clearEvent 655]
private def ctx9735 (s : BitVec 37) : BitVec 37 := (bit s 6) ^^^ (bit s 27) ^^^ (bit s 6 &&& bit s 27) ^^^ (bit s 14 &&& bit s 27)

theorem concrete_9735 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 29 ^^^ bit s 35) &&& (ctx9735 s ^^^ bit s 29) = 0) :
    run src9735 (s,phase,event) = lift (run dst9735 (s,phase,event)) := by
  apply Prod.ext
  · unfold src9735 dst9735 ctx9735 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_9735 :
    src9735.all (wireOK 37) = true ∧ dst9735.all (wireOK 36) = true ∧
    paid src9735 = 1 ∧ paid dst9735 = 3 := by decide


private def src10041 : List Gate := [.cx 35 18, .cx 35 29, .ccx 18 29 36, .cx 35 36, .cx 35 18, .cx 18 29, .hmr0 35 677]
private def dst10041 : List Gate := [.cx 29 35, .cx 6 3, .cx 27 3, .cx 17 16, .ccx 3 16 18, .cx 17 16, .cx 27 3, .cx 6 3, .x 18, .cx 16 18, .ccx 35 18 29, .cx 16 18, .x 18, .cx 6 3, .cx 27 3, .cx 17 16, .ccx 3 16 18, .cx 17 16, .cx 27 3, .cx 6 3, .cx 18 35, .swap 29 35, .clearEvent 677]
private def ctx10041 (s : BitVec 37) : BitVec 37 := (1 : BitVec 37) ^^^ (bit s 16) ^^^ (bit s 3 &&& bit s 16) ^^^ (bit s 3 &&& bit s 17) ^^^ (bit s 6 &&& bit s 16) ^^^ (bit s 6 &&& bit s 17) ^^^ (bit s 16 &&& bit s 27) ^^^ (bit s 17 &&& bit s 27)

theorem concrete_10041 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 29 ^^^ bit s 35) &&& (ctx10041 s ^^^ bit s 29) = 0) :
    run src10041 (s,phase,event) = lift (run dst10041 (s,phase,event)) := by
  apply Prod.ext
  · unfold src10041 dst10041 ctx10041 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_10041 :
    src10041.all (wireOK 37) = true ∧ dst10041.all (wireOK 36) = true ∧
    paid src10041 = 1 ∧ paid dst10041 = 3 := by decide


private def src10114 : List Gate := [.cx 35 19, .cx 35 29, .ccx 19 29 36, .cx 35 36, .cx 35 19, .cx 19 29, .hmr0 35 682]
private def dst10114 : List Gate := [.cx 29 35, .cx 6 2, .cx 27 2, .cx 18 17, .ccx 2 17 19, .cx 18 17, .cx 27 2, .cx 6 2, .x 19, .cx 17 19, .ccx 35 19 29, .cx 17 19, .x 19, .cx 6 2, .cx 27 2, .cx 18 17, .ccx 2 17 19, .cx 18 17, .cx 27 2, .cx 6 2, .cx 19 35, .swap 29 35, .clearEvent 682]
private def ctx10114 (s : BitVec 37) : BitVec 37 := (1 : BitVec 37) ^^^ (bit s 17) ^^^ (bit s 2 &&& bit s 17) ^^^ (bit s 2 &&& bit s 18) ^^^ (bit s 6 &&& bit s 17) ^^^ (bit s 6 &&& bit s 18) ^^^ (bit s 17 &&& bit s 27) ^^^ (bit s 18 &&& bit s 27)

theorem concrete_10114 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 29 ^^^ bit s 35) &&& (ctx10114 s ^^^ bit s 29) = 0) :
    run src10114 (s,phase,event) = lift (run dst10114 (s,phase,event)) := by
  apply Prod.ext
  · unfold src10114 dst10114 ctx10114 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_10114 :
    src10114.all (wireOK 37) = true ∧ dst10114.all (wireOK 36) = true ∧
    paid src10114 = 1 ∧ paid dst10114 = 3 := by decide


private def src10175 : List Gate := [.cx 35 20, .cx 35 29, .ccx 20 29 36, .cx 35 36, .cx 35 20, .cx 20 29, .hmr0 35 686]
private def dst10175 : List Gate := [.cx 29 35, .cx 6 1, .cx 27 1, .cx 19 18, .ccx 1 18 20, .cx 19 18, .cx 27 1, .cx 6 1, .x 20, .cx 18 20, .ccx 35 20 29, .cx 18 20, .x 20, .cx 6 1, .cx 27 1, .cx 19 18, .ccx 1 18 20, .cx 19 18, .cx 27 1, .cx 6 1, .cx 20 35, .swap 29 35, .clearEvent 686]
private def ctx10175 (s : BitVec 37) : BitVec 37 := (1 : BitVec 37) ^^^ (bit s 18) ^^^ (bit s 1 &&& bit s 18) ^^^ (bit s 1 &&& bit s 19) ^^^ (bit s 6 &&& bit s 18) ^^^ (bit s 6 &&& bit s 19) ^^^ (bit s 18 &&& bit s 27) ^^^ (bit s 19 &&& bit s 27)

theorem concrete_10175 (s : BitVec 37) (phase event : Bool)
    (hz : bit s 36 = 0)
    (hc : (bit s 29 ^^^ bit s 35) &&& (ctx10175 s ^^^ bit s 29) = 0) :
    run src10175 (s,phase,event) = lift (run dst10175 (s,phase,event)) := by
  apply Prod.ext
  · unfold src10175 dst10175 ctx10175 at *
    simp only [run, List.foldl_cons, List.foldl_nil, step, lift, bit, toggle, clear, Prod.fst, Prod.snd] at *
    bv_decide
  · rfl

theorem resource_10175 :
    src10175.all (wireOK 37) = true ∧ dst10175.all (wireOK 36) = true ∧
    paid src10175 = 1 ∧ paid dst10175 = 3 := by decide

end GVQCC.ActualContextBridge
