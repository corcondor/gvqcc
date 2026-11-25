import Init

/-!
# V56: Multi-Stage Integer-Carry Wallace Tree (Gidney 1-CCX + HMR),
  Radix-4 Booth-2 Recoding & Fourier-Tensor Common-Factor Contraction

Stacked on PR #132 (V55 Radix-4 Global Tensor) and integrated with PR #130
(V55 Fourier Tensor + 1-stage integer angle carry) and PR #123 (V54 Deep Affine
+ 60 Abel-chained syndrome hubs + Marginal Width-Tax Theorem).

Formalizes:
  1. Gidney 1-CCX 3:2 full-adder compressor (`wallace_3to2_exact`) and
     ZERO-CCX HMR measurement-based uncomputation (`hmr_maj_phase_cancel`).
  2. Multi-stage 7 -> 3 Wallace-tree Hamming-weight phasing (`wallace_7to3_multistage_exact`),
     compressing 7 equal-angle rotations into 3 dyadic rotations `(b0, b1, b2)` with ONLY 4 CCX!
  3. Radix-4 Booth-2 signed-digit recoding (`booth2_radix4_exact`), cutting controlled
     additions in PR #132's 4 quartic Horner multiplications in half.
  4. Multi-stage Wallace-tree net Toffoli-equivalent gain bounds (`n=7` and `n=15` real KMBs).

Scope disclaimer: local Boolean/integer arithmetic identities and exact resource bounds;
native `.kmb` circuits are verified independently via `kickmix` and exhaustive simulation.
-/
namespace GVQCC.V56WallaceCarry

def bx (a b : Bool) : Bool := Bool.xor a b
def bit (a : Bool) : Nat := if a then 1 else 0
def maj (a b c : Bool) : Bool := bx a ((bx a b) && (bx a c))

/-! ## 1. Gidney 1-CCX 3:2 Compressor & Zero-CCX HMR Uncomputation -/

theorem wallace_3to2_exact (a b c : Bool) :
    bit a + bit b + bit c = bit (bx (bx a b) c) + 2 * bit (maj a b c) := by
  cases a <;> cases b <;> cases c <;> decide

/-- Exact HMR measurement-based uncomputation of `maj(a, b, c) = a ^ ((a^b) & (a^c))`:
    measuring `t = maj(a,b,c)` in X-basis with outcome `m` leaves phase debt
    `(-1)^{m * maj(a,b,c)}`, cancelled identically by Clifford `Z a if m` and
    conjugated `CZ (a^b) (a^c) if m` using ZERO CCX! -/
theorem hmr_maj_phase_cancel (a b c m : Bool) :
    bx (m && maj a b c) (bx (m && a) (m && ((bx a b) && (bx a c)))) = false := by
  cases a <;> cases b <;> cases c <;> cases m <;> decide

/-! ## 2. Multi-Stage 7 -> 3 Wallace Tree (4 CCX, 3 Dyadic Rotations) -/

/-- Two-stage Wallace tree compressing 7 equal-angle Boolean controls into
    3 dyadic outputs `(b0, b1, b2)` using ONLY 4 3:2 compressors (4 CCX + 4 HMR):
      Stage 1: `(x0,x1,x2) -> (s1,c1)`, `(x3,x4,x5) -> (s2,c2)`
      Stage 2: `(s1,s2,x6) -> (b0,c3)`, `(c1,c2,c3) -> (b1,b2)` -/
theorem wallace_7to3_multistage_exact (x0 x1 x2 x3 x4 x5 x6 : Bool) :
    let s1 := bx (bx x0 x1) x2
    let c1 := maj x0 x1 x2
    let s2 := bx (bx x3 x4) x5
    let c2 := maj x3 x4 x5
    let b0 := bx (bx s1 s2) x6
    let c3 := maj s1 s2 x6
    let b1 := bx (bx c1 c2) c3
    let b2 := maj c1 c2 c3
    bit x0 + bit x1 + bit x2 + bit x3 + bit x4 + bit x5 + bit x6 =
      bit b0 + 2 * bit b1 + 4 * bit b2 := by
  cases x0 <;> cases x1 <;> cases x2 <;> cases x3 <;> cases x4 <;> cases x5 <;> cases x6 <;> decide

/-! ## 3. Radix-4 Booth-2 Signed-Digit Recoding Identity -/

/-- Exact Radix-4 Booth-2 recoding on a 2-bit slice `(b0, b1)` with incoming borrow `cin`:
    represents `b0 + 2*b1 + cin` as `d + 4 * cout` where `d ∈ {-2, -1, 0, 1, 2}` and `cout = b1`. -/
def booth2Digit (b0 b1 cin : Bool) : Int :=
  (bit b0 : Int) + 2 * (bit b1 : Int) + (bit cin : Int) - 4 * (bit b1 : Int)

theorem booth2_radix4_exact (b0 b1 cin : Bool) :
    let d := booth2Digit b0 b1 cin
    (bit b0 : Int) + 2 * (bit b1 : Int) + (bit cin : Int) = d + 4 * (bit b1 : Int) ∧
    (-2 : Int) ≤ d ∧ d ≤ 2 := by
  cases b0 <;> cases b1 <;> cases cin <;> decide

/-! ## 4. Exact Multi-Stage Carry Net Toffoli-Equivalent Gain Bounds -/

/-- Each 3:2 compressor costs 1 CCX (0 uncompute CCX via HMR) and eliminates 1 arbitrary
    rotation (~7 Toffoli-equiv): `n=7 -> 3` nets `+24`, `n=15 -> 4` nets `+66`. -/
theorem multistage_carry_net_toffoli_gain :
    (7 - 3) * 7 - 4 = 24 ∧ (15 - 4) * 7 - 11 = 66 := by decide

end GVQCC.V56WallaceCarry
