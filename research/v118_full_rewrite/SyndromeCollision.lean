import Init
namespace GVQCC.SyndromeCollision
set_option maxRecDepth 100000
set_option maxHeartbeats 0

-- GF(4096): x^12+x^6+x^4+x+1, primitive element 2.
def mulLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, z => z
  | n+1, a, b, z =>
    let d := 2*a
    mulLoop n (if d ≥ 4096 then Nat.xor d 4179 else d)
      (b/2) (if b%2 == 1 then Nat.xor z a else z)
def gm (a b : Nat) := mulLoop 12 a b 0
def powLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, z => z
  | n+1, a, e, z =>
    powLoop n (gm a a) (e/2) (if e%2 == 1 then gm z a else z)
def alpha (p : Nat) := powLoop 12 2 (p%4095) 1
def advance (p : Nat × Nat) := (p.1, gm p.1 p.2)
def init (w : List (Nat × Nat)) :=
  w.map (fun p => let a := alpha p.1; (a,gm a p.2))
def rows : Nat → List (Nat × Nat) → List Nat
  | 0, _ => []
  | n+1, w => (w.foldl (fun z p => Nat.xor z p.2) 0) :: rows n (w.map advance)
def moments (w : List (Nat × Nat)) := rows 70 (init w)
def truth : List (Nat × Nat) := [(734, 2817), (2106, 3571), (3499, 705), (2515, 204), (4070, 3211), (843, 2604), (2140, 118), (477, 62), (2577, 2707), (3818, 2219), (4052, 1373), (2517, 401), (3531, 1933), (280, 1968), (1352, 2104), (2419, 2738), (2333, 193), (1648, 3957), (1347, 960), (36, 1361), (4057, 4092), (2367, 3149), (1318, 3394), (2298, 2023), (2433, 105), (1051, 1477), (599, 1914), (688, 2584), (3993, 3638)]
def observedCandidate : List (Nat × Nat) := [(0, 688), (1, 2408), (2, 3577), (3, 1017), (4, 700), (5, 1174), (6, 1716), (7, 2835), (8, 232), (9, 230), (10, 2822), (11, 3517), (12, 3763), (13, 1527), (14, 2492), (15, 2910), (16, 3554), (17, 2197), (18, 3425), (19, 30), (20, 1784), (21, 3629), (22, 606), (23, 3126), (24, 1690), (25, 3803), (26, 2490), (27, 2162), (28, 3325), (29, 3650), (30, 3448), (31, 1335), (32, 3820), (33, 65), (34, 3014), (35, 1258), (36, 1446), (37, 845), (38, 2105), (39, 3817), (40, 1796), (41, 640), (42, 2373), (43, 1096), (44, 3310), (45, 2278), (46, 592), (47, 710), (48, 2872), (49, 3679), (50, 861), (51, 2971), (52, 547), (53, 1260), (54, 4002), (55, 1524), (56, 1290), (57, 1366), (58, 1625), (59, 1454), (60, 3904), (61, 2741), (62, 1547), (63, 2108), (64, 2080), (65, 1074), (66, 3716), (67, 954), (68, 3827), (69, 52), (2990, 1433)]
def syndrome : List Nat := [65,3524,3353,3707,2476,2123,3403,3397,3402,3684,853,2077,1375,3187,3087,107,4001,3854,2517,2399,3855,1840,71,4016,348,769,2671,2845,2760,1130,1530,2429,21,773,1124,1351,228,1321,1360,17,895,180,3014,2063,1663,2055,1501,1198,2367,3662,2799,1119,2700,1548,3386,4010,357,753,2347,2598,3582,341,3618,3351,551,1842,2644,2405,12,702]
def validWord (w : List (Nat × Nat)) : Bool :=
  w.all (fun p => p.1 < 4095 && 0 < p.2 && p.2 < 4096) &&
  ((w.map Prod.fst).eraseDups.length == w.length)

theorem truth_shape : truth.length = 29 ∧ validWord truth = true := by decide
theorem observed_shape : observedCandidate.length = 71 ∧ validWord observedCandidate = true := by decide
theorem truth_syndromes : moments truth = syndrome := by decide
theorem observed_syndromes : moments observedCandidate = syndrome := by decide
theorem collision : moments truth = moments observedCandidate := by
  rw [truth_syndromes, observed_syndromes]
theorem not_same : truth ≠ observedCandidate := by decide

-- An arbitrary solution of the syndrome equations need not be the bounded
-- weight solution. This is a concrete witness, not a whole-circuit proof.
#print axioms truth_shape
#print axioms observed_shape
#print axioms truth_syndromes
#print axioms observed_syndromes
#print axioms collision
#print axioms not_same
end GVQCC.SyndromeCollision
