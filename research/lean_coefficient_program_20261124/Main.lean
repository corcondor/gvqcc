import GVQCCProgram
open GVQCCProgram

structure Problem where
  width : Nat
  full : Nat
  budget : Nat
  initial : List Nat
  target : List Nat
  gates : List Gate

def nums (s : String) : Except String (List Nat) :=
  (s.splitOn " ").mapM fun x =>
    match x.toNat? with
    | some n => .ok n
    | none => .error ("not a natural number: " ++ x)

def parseGate (xs : List Nat) : Except String Gate :=
  match xs with
  | [17,t] => .ok (.x t)
  | [33,a,t] => .ok (.cx a t)
  | [49,a,b,t] => .ok (.ccx a b t)
  | [80,t,j] => .ok (.hmr t j)
  | [16,t] => .ok (.z t)
  | [32,a,b] => .ok (.cz a b)
  | [144,t,j] => .ok (.zIf t j)
  | [160,a,b,j] => .ok (.czIf a b j)
  | _ => .error "unsupported gate or malformed arguments"

def parseProblem (s : String) : Except String Problem := do
  match (s.splitOn "\n").filter (fun x => x != "") with
  | h :: input :: output :: lines =>
    match ← nums h with
    | [n,full,budget] =>
      let initial ← nums input
      let target ← nums output
      let gates ← lines.mapM (fun l => do parseGate (← nums l))
      return ⟨n,full,budget,initial,target,gates⟩
    | _ => throw "expected width full_mask budget"
  | _ => throw "expected header, initial and target"

def verifyFile (path : String) : IO (Bool × Nat) := do
  match parseProblem (← IO.FS.readFile path) with
  | .error e =>
    IO.eprintln e
    return (false,0)
  | .ok p =>
    let ok := check p.width p.full p.budget p.initial p.target p.gates
    let cost := paid p.gates
    IO.println s!"{path}: accepted={ok} paid={cost} Q={p.width} HMR={events p.gates}"
    return (ok,cost)

def main (args : List String) : IO UInt32 := do
  if args.isEmpty then
    IO.eprintln "usage: lean --run Main.lean bank.txt [more banks...]"
    return 2
  let mut ok := true
  let mut cost := 0
  for path in args do
    let (b,t) ← verifyFile path
    ok := ok && b
    cost := cost + t
  IO.println s!"accepted_all={ok} total_paid={cost}"
  return if ok then 0 else 1
