#!/usr/bin/env python3
"""Public V8 W sparsity -> self-contained Lean 4.35 kernel certificate.
GitHub Actions fetches the SHA-pinned Kaggle V8 NPZ, never executes notebook cells.
NOTE: exact zero coefficients in W do NOT directly correspond to ANGLE Toffoli gates.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

NPZ_SHA="d4d39b2e2516ed7c51a936e863cf0567e558a0db8ded24e435f507d76bfb78d7"
W_SHA="07133824492ef24ae9aae5e878b2c2af539b1c44ec3382f7a164a9e365af9d3a"

def build(npz,lean):
    npz=Path(npz);lean=Path(lean)
    assert hashlib.sha256(npz.read_bytes()).hexdigest()==NPZ_SHA,"wrong public V8 input SHA"
    with np.load(npz,allow_pickle=False) as z: W=np.array(z["W"],dtype=np.float64)
    assert W.shape==(9,127,46) and np.isfinite(W).all()
    assert hashlib.sha256(W.tobytes()).hexdigest()==W_SHA,"wrong W tensor"
    masks=[sum(1<<c for c in range(46) if W[r,b,c]!=0)
           for r in range(9) for b in range(127)]
    cards=[int(v).bit_count() for v in masks]
    assert len(cards)==1143 and sum(cards)==41437
    assert min(cards)==7 and all(cards) and sum(v==46 for v in cards)==141
    assert sum(v<=23 for v in cards)==74
    assert [c for c in range(46) if masks[8*127+79]>>c&1]==[8,13,19,21,34,37,42]
    assert [sum(cards[127*r:127*(r+1)]) for r in range(9)]==[4625,4595,4932,4559,4507,4428,4518,4655,4618]
    out=[
      "/- Exact-support Lean certificate of real V8 W coefficients.",
      "NPZ SHA256: "+NPZ_SHA,
      "W IEEE-754 bytes SHA256: "+W_SHA,
      "Neither a new KMB nor a bound on optimized Toffoli cost. -/",
      "import Init",
      "namespace GVQCC.SparseW",
      "set_option maxRecDepth 16384",
      "def supportRows : Array Nat := #["]
    for i in range(0,1143,8):
        out.append("  "+", ".join(f"0x{v:012x}" for v in masks[i:i+8])+("," if i+8<1143 else ""))
    out+=["]", "def rowDegrees : Array Nat := #["]
    for i in range(0,1143,32):
        out.append("  "+", ".join(str(v) for v in cards[i:i+32])+("," if i+32<1143 else ""))
    out += [
      "]",
      "def rowDegree (i : Nat) : Nat :=",
      "  (List.range 46).foldl (fun n c => n + if Nat.testBit (supportRows[i]!) c then 1 else 0) 0",
      "def degreeChecks (r : Nat) : Bool :=",
      "  (List.range 127).all (fun b => rowDegree (127*r+b) == rowDegrees[127*r+b]!)",
    ]
    for r in range(9):out.append(f"theorem verified_row_degrees_{r} : degreeChecks {r} = true := by decide")
    out += [
      "/-- The raw data has no whole (r,b) W-row consisting of zeros. -/",
      "theorem all_rows_have_some_nonzero_W :",
      "  (List.range 1143).all (fun i => supportRows[i]! != 0) = true := by decide",
      "def totalNonzero : Nat := rowDegrees.toList.foldl (fun s n => s+n) 0",
      "theorem exact_nonzero_count : totalNonzero = 41437 := by decide",
      "theorem exact_zero_count : 1143 * 46 - totalNonzero = 11141 := by decide",
      "def sparseRows : Nat := (rowDegrees.toList.filter (fun n => n <= 23)).length",
      "def denseRows : Nat := (rowDegrees.toList.filter (fun n => n == 46)).length",
      "theorem few_channel_rows : sparseRows = 74 := by decide",
      "theorem completely_dense_rows : denseRows = 141 := by decide",
      "theorem very_sparse_row : rowDegree (8*127+79) = 7 := by decide",
      "theorem very_sparse_row_mask : supportRows[8*127+79]! =",
      "  (2^8+2^13+2^19+2^21+2^34+2^37+2^42) := by decide",
      "",
      "/-- Exact coefficient contraction: every zero term can be deleted.",
      "    The vector components could be anything, including U_{rb,i}U_{rb,j}. -/",
      "def dot : List (Int × Int) → Int",
      " | [] => 0",
      " | (w,x) :: rest => w*x + dot rest",
      "def sparseDot : List (Int × Int) → Int",
      " | [] => 0",
      " | (w,x) :: rest => if w = 0 then sparseDot rest else w*x+sparseDot rest",
      "theorem sparse_dot_equal_full (t : List (Int × Int)) : sparseDot t = dot t := by",
      " induction t with",
      " | nil => rfl",
      " | cons p ps ih =>",
      "   rcases p with ⟨w,x⟩",
      "   by_cases hz : w = 0",
      "   · simp [sparseDot,dot,hz,ih]",
      "   · simp [sparseDot,dot,hz,ih]",
      "/-- A nonzero abstract coefficient has a nonzero basis witness.",
      "    Does not rule out cancellation among concrete U-projectors. -/",
      "theorem nonzero_has_witness (w : Int) (hw : w != 0) : w*1 != 0 := by",
      " simpa using hw",
      "end GVQCC.SparseW"
    ]
    lean.parent.mkdir(parents=True,exist_ok=True)
    lean.write_text("\n".join(out)+"\n",encoding="utf8")
    outj={"source_npz_sha256":NPZ_SHA,"W_sha256":W_SHA,
          "masked_contraction_terms":sum(cards),"zero_terms":1143*46-sum(cards),
          "nonempty_W_rows":1143,"empty_W_rows":0,"sparse_rows_degree_le_23":74,
          "fully_dense_rows":141,"min_support_row":[8,79],"min_support_channels":[8,13,19,21,34,37,42],
          "unique_support_masks":len(set(masks)),
          "lean_source_sha256":hashlib.sha256(lean.read_bytes()).hexdigest(),
          "status":"coefficient_zero_elimination_only_NOT_KMB_T_reduction"}
    lean.with_suffix(".json").write_text(json.dumps(outj,indent=2)+"\n")
    print(json.dumps(outj,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--npz",required=True);ap.add_argument("--lean",required=True)
    a=ap.parse_args();build(a.npz,a.lean)
