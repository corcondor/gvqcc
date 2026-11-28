import Std.Tactic.BVDecide
namespace GVQCCV7
-- Actual KMB source interval [25709,25759); native destination 59 instructions.
-- q0..8 correspond to logical q6,q10,q12,q22,q24,q29,q31,q33,q35.
-- q10 and omitted q29 are zero on entry. Unused wires are unchanged.
-- c0..2 correspond to c482,c481,c483; c3 is fresh, unobserved.
-- SSA operations generated from the literal gates below, with versioned HMR outcomes.
def sourceGates : List (List Nat) := [[129,0],[33,4,8],[33,0,4],[17,8],[49,4,8,1],[144,2,1],[33,1,4],[33,0,4],[144,4,1],[33,2,7],[160,2,7,1],[160,2,4,1],[160,4,7,1],[33,4,7],[33,2,4],[17,7],[49,4,7,5],[16,3],[33,4,5],[33,2,5],[16,5],[33,3,6],[32,3,6],[32,3,5],[32,5,6],[80,5,2,0],[144,2,2],[33,2,4],[144,4,2],[33,4,7],[17,7],[160,2,7,2],[160,2,4,2],[160,4,7,2],[33,8,1],[33,4,1],[17,1],[80,4,2,1],[144,0,2],[33,1,8],[17,8],[144,8,2],[160,0,1,2],[160,0,8,2],[160,1,8,2],[34,1,4],[34,8,4],[33,3,6],[33,2,7],[1]]
def candidateGates : List (List Nat) := [[129,0],[80,1,2,0],[80,1,2,1],[1],[129,0],[17,4],[33,8,4],[17,0],[33,8,0],[33,4,0],[49,0,4,1],[33,4,0],[33,8,0],[17,0],[33,8,4],[17,4],[33,2,1],[33,4,1],[1],[129,0],[32,0,4],[16,4],[32,2,6],[32,0,8],[32,3,6],[32,4,8],[16,0],[32,1,6],[32,1,7],[1],[129,0],[129,1],[32,0,8],[16,4],[32,0,4],[32,4,8],[16,0],[32,1,7],[1],[1],[129,0],[48,6,7,1],[1],[129,0],[33,4,1],[33,2,1],[17,4],[33,8,4],[17,0],[33,8,0],[33,4,0],[80,1,3,2],[160,0,4,3],[33,4,0],[33,8,0],[17,0],[33,8,4],[17,4],[1]]
def source (q0 q2 q3 q4 q6 q7 q8 c0 c1 c2 m0 m1 m2 p : Bool) : List Bool :=
  let v1 := (true && c0)
  let v2 := Bool.xor (q8) ((v1 && q4))
  let v3 := Bool.xor (q4) ((v1 && q0))
  let v4 := Bool.xor (v2) ((v1))
  let v5 := Bool.xor (false) ((v1 && v3 && v4))
  let v6 := Bool.xor (p) (((v1 && c1) && q2))
  let v7 := Bool.xor (v3) ((v1 && v5))
  let v8 := Bool.xor (v7) ((v1 && q0))
  let v9 := Bool.xor (v6) (((v1 && c1) && v8))
  let v10 := Bool.xor (q7) ((v1 && q2))
  let v11 := Bool.xor (v9) (((v1 && c1) && q2 && v10))
  let v12 := Bool.xor (v11) (((v1 && c1) && q2 && v8))
  let v13 := Bool.xor (v12) (((v1 && c1) && v8 && v10))
  let v14 := Bool.xor (v10) ((v1 && v8))
  let v15 := Bool.xor (v8) ((v1 && q2))
  let v16 := Bool.xor (v14) ((v1))
  let v17 := Bool.xor (false) ((v1 && v15 && v16))
  let v18 := Bool.xor (v13) ((v1 && q3))
  let v19 := Bool.xor (v17) ((v1 && v15))
  let v20 := Bool.xor (v19) ((v1 && q2))
  let v21 := Bool.xor (v18) ((v1 && v20))
  let v22 := Bool.xor (q6) ((v1 && q3))
  let v23 := Bool.xor (v21) ((v1 && q3 && v22))
  let v24 := Bool.xor (v23) ((v1 && q3 && v20))
  let v25 := Bool.xor (v24) ((v1 && v20 && v22))
  let v26 := Bool.xor (v25) ((v1 && v20 && m0))
  let v27 := (v20 && (!v1))
  let v28 := if v1 then m0 else c2
  let v29 := Bool.xor (v26) (((v1 && v28) && q2))
  let v30 := Bool.xor (v15) ((v1 && q2))
  let v31 := Bool.xor (v29) (((v1 && v28) && v30))
  let v32 := Bool.xor (v16) ((v1 && v30))
  let v33 := Bool.xor (v32) ((v1))
  let v34 := Bool.xor (v31) (((v1 && v28) && q2 && v33))
  let v35 := Bool.xor (v34) (((v1 && v28) && q2 && v30))
  let v36 := Bool.xor (v35) (((v1 && v28) && v30 && v33))
  let v37 := Bool.xor (v5) ((v1 && v4))
  let v38 := Bool.xor (v37) ((v1 && v30))
  let v39 := Bool.xor (v38) ((v1))
  let v40 := Bool.xor (v36) ((v1 && v30 && m1))
  let v41 := (v30 && (!v1))
  let v42 := if v1 then m1 else v28
  let v43 := Bool.xor (v40) (((v1 && v42) && q0))
  let v44 := Bool.xor (v4) ((v1 && v39))
  let v45 := Bool.xor (v44) ((v1))
  let v46 := Bool.xor (v43) (((v1 && v42) && v45))
  let v47 := Bool.xor (v46) (((v1 && v42) && q0 && v39))
  let v48 := Bool.xor (v47) (((v1 && v42) && q0 && v45))
  let v49 := Bool.xor (v48) (((v1 && v42) && v39 && v45))
  let v50 := (v1 && Bool.xor (v39) (v41))
  let v51 := Bool.xor (v39) (v50)
  let v52 := Bool.xor (v41) (v50)
  let v53 := (v1 && Bool.xor (v45) (v52))
  let v54 := Bool.xor (v45) (v53)
  let v55 := Bool.xor (v52) (v53)
  let v56 := Bool.xor (v22) ((v1 && q3))
  let v57 := Bool.xor (v33) ((v1 && q2))
  [q0, v51, q2, q3, v55, v27, v56, v57, v54, c0, c1, v42, v49]
def candidate (q0 q2 q3 q4 q6 q7 q8 c0 c1 c2 m0 m1 m2 p : Bool) : List Bool :=
  let v1 := (true && c0)
  let v2 := Bool.xor (p) ((v1 && false && m0))
  let v3 := (false && (!v1))
  let v4 := if v1 then m0 else c2
  let v5 := Bool.xor (v2) ((v1 && v3 && m1))
  let v6 := (v3 && (!v1))
  let v7 := if v1 then m1 else v4
  let v8 := (true && c0)
  let v9 := Bool.xor (q4) ((v8))
  let v10 := Bool.xor (v9) ((v8 && q8))
  let v11 := Bool.xor (q0) ((v8))
  let v12 := Bool.xor (v11) ((v8 && q8))
  let v13 := Bool.xor (v12) ((v8 && v10))
  let v14 := Bool.xor (v6) ((v8 && v13 && v10))
  let v15 := Bool.xor (v13) ((v8 && v10))
  let v16 := Bool.xor (v15) ((v8 && q8))
  let v17 := Bool.xor (v16) ((v8))
  let v18 := Bool.xor (v10) ((v8 && q8))
  let v19 := Bool.xor (v18) ((v8))
  let v20 := Bool.xor (v14) ((v8 && q2))
  let v21 := Bool.xor (v20) ((v8 && v19))
  let v22 := (true && c0)
  let v23 := Bool.xor (v5) ((v22 && v17 && v19))
  let v24 := Bool.xor (v23) ((v22 && v19))
  let v25 := Bool.xor (v24) ((v22 && q2 && q6))
  let v26 := Bool.xor (v25) ((v22 && v17 && q8))
  let v27 := Bool.xor (v26) ((v22 && q3 && q6))
  let v28 := Bool.xor (v27) ((v22 && v19 && q8))
  let v29 := Bool.xor (v28) ((v22 && v17))
  let v30 := Bool.xor (v29) ((v22 && v21 && q6))
  let v31 := Bool.xor (v30) ((v22 && v21 && q7))
  let v32 := (true && c0)
  let v33 := (v32 && c1)
  let v34 := Bool.xor (v31) ((v33 && v17 && q8))
  let v35 := Bool.xor (v34) ((v33 && v19))
  let v36 := Bool.xor (v35) ((v33 && v17 && v19))
  let v37 := Bool.xor (v36) ((v33 && v19 && q8))
  let v38 := Bool.xor (v37) ((v33 && v17))
  let v39 := Bool.xor (v38) ((v33 && v21 && q7))
  let v40 := (true && c0)
  let v41 := Bool.xor (v39) ((v40 && q6 && q7 && v21))
  let v42 := (true && c0)
  let v43 := Bool.xor (v21) ((v42 && v19))
  let v44 := Bool.xor (v43) ((v42 && q2))
  let v45 := Bool.xor (v19) ((v42))
  let v46 := Bool.xor (v45) ((v42 && q8))
  let v47 := Bool.xor (v17) ((v42))
  let v48 := Bool.xor (v47) ((v42 && q8))
  let v49 := Bool.xor (v48) ((v42 && v46))
  let v50 := Bool.xor (v41) ((v42 && v44 && m2))
  let v51 := (v44 && (!v42))
  let v52 := if v42 then m2 else false
  let v53 := Bool.xor (v50) (((v42 && v52) && v49 && v46))
  let v54 := Bool.xor (v49) ((v42 && v46))
  let v55 := Bool.xor (v54) ((v42 && q8))
  let v56 := Bool.xor (v55) ((v42))
  let v57 := Bool.xor (v46) ((v42 && q8))
  let v58 := Bool.xor (v57) ((v42))
  [v56, v51, q2, q3, v58, false, q6, q7, q8, c0, c1, v7, v53]
theorem actual_25709 (q0 q2 q3 q4 q6 q7 q8 c0 c1 c2 m0 m1 m2 p : Bool) :
    source q0 q2 q3 q4 q6 q7 q8 c0 c1 c2 m0 m1 m2 p =
    candidate q0 q2 q3 q4 q6 q7 q8 c0 c1 c2 m0 m1 m2 p := by
  simp [source, candidate] <;> bv_decide

def paid (g : List (List Nat)) : Nat :=
  (g.filter (fun o => [48,49,50].contains (o.headD 0 % 128))).length
def wires (g : List Nat) : List Nat :=
  g.tail.take (if [17,16,80,144].contains (g.headD 0) then 1 else
    if [33,34,32,160].contains (g.headD 0) then 2 else
    if [48,49,50].contains (g.headD 0) then 3 else 0)
def physical (i : Nat) : Nat := [6,10,12,22,24,29,31,33,35].getD i 37
theorem resources : sourceGates.length = 50 ∧ candidateGates.length = 59 ∧
    paid sourceGates = 2 ∧ paid candidateGates = 2 ∧
    candidateGates.all (fun g => (wires g).all (fun i => physical i < 36 && i != 5)) = true := by decide
end GVQCCV7
