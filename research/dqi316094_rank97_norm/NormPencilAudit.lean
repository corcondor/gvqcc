import Std
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace NormPencilAudit
-- Concrete alternating polar matrices, in the second 24-bit operand chart.
def pencil : List (List Nat) := [[9273056,13014896,10949424,16326928,14214926,7108871,8007939,10424833,12660862,4329623,16269331,6062113,1836007,2359673,9372721,12912658,14729613,7357126,3209383,1072377,924888,468076,233338,116127],[13014896,4974992,16326928,6173216,7108871,11836937,10424833,15016706,4329623,8593641,6062113,10797106,2359673,3670686,12912658,4852771,7357126,9470795,1072377,2139230,468076,604340,116127,150245],[6173216,10949424,13847744,6390848,15016706,8007939,4047884,1460228,10797106,16269331,6680652,12210308,4852771,9372721,5640132,11208008,2139230,3209383,12608979,4242017,150245,233338,808509,305942],[10949424,16326928,6390848,11716736,8007939,10424833,1460228,2853896,16269331,6062113,12210308,14655688,9372721,12912658,11208008,16583308,3209383,1072377,4242017,8445874,233338,116127,305942,589099],[1408608,2791344,9245584,12984800,5367558,10647819,14168329,7082510,1986686,2597015,8638483,12673057,14747111,7473785,3673393,1836562,7701,10026,33677,49606,57681,29346,14552,7276],[2791344,4188624,12984800,4928112,10647819,15965709,7082510,11805447,2597015,3797225,12673057,4370482,7473785,9637790,1836562,2362147,10026,14655,49606,16971,29346,37875,7276,9396],[4928112,9245584,6179856,10978336,11805447,14168329,15057921,8013826,4370482,8638483,6086732,10776708,2362147,3673393,12914372,4851528,16971,33677,23646,42151,9396,14552,50661,19066],[9245584,12984800,10978336,16369712,14168329,7082510,8013826,10456067,8638483,12673057,10776708,16289992,3673393,1836562,4851528,9374092,33677,49606,42151,63737,14552,7276,19066,36767],[1410208,2803952,9282912,13040304,5326858,10652687,14178822,7122699,20612,41160,53413,24826,1352,2700,3418,1711,21,42,141,198,81,162,216,108],[2803952,4148304,13040304,4939728,10652687,15975429,7122699,11859213,41160,61516,24826,45151,2700,4036,1711,3061,42,63,198,75,162,243,108,180],[6216560,10972560,13860368,6395680,15056135,8050185,4056833,1472770,57563,28781,12414,4247,3773,2006,999,377,94,167,211,97,229,122,61,22],[10972560,16365280,6395680,11725104,8050185,10447630,1472770,2858499,28781,37046,4247,8425,2006,2411,377,670,167,249,97,178,122,159,22,43]]
def combination (m : Nat) : List Nat :=
  (List.range 12).foldl
    (fun acc i => if m.testBit i then List.zipWith Nat.xor acc (pencil[i]?.getD []) else acc)
    (List.replicate 24 0)
def nonsingular : Nat → List Nat → Bool
  | 0, rows => rows.isEmpty
  | n+1, rows =>
    match rows.find? (fun r => r.testBit n) with
    | none => false
    | some p => nonsingular n ((rows.erase p).map (fun r => if r.testBit n then Nat.xor r p else r))
-- Finite certificate, not a reachability proof or a general tensor rank bound.
def check (start : Nat) : Bool :=
  (List.range 64).all (fun i => let m := start+i; m == 0 || nonsingular 24 (combination m))
theorem block_0 : check 0 = true := by decide
#print axioms block_0
theorem block_1 : check 64 = true := by decide
#print axioms block_1
theorem block_2 : check 128 = true := by decide
#print axioms block_2
theorem block_3 : check 192 = true := by decide
#print axioms block_3
theorem block_4 : check 256 = true := by decide
#print axioms block_4
theorem block_5 : check 320 = true := by decide
#print axioms block_5
theorem block_6 : check 384 = true := by decide
#print axioms block_6
theorem block_7 : check 448 = true := by decide
#print axioms block_7
theorem block_8 : check 512 = true := by decide
#print axioms block_8
theorem block_9 : check 576 = true := by decide
#print axioms block_9
theorem block_10 : check 640 = true := by decide
#print axioms block_10
theorem block_11 : check 704 = true := by decide
#print axioms block_11
theorem block_12 : check 768 = true := by decide
#print axioms block_12
theorem block_13 : check 832 = true := by decide
#print axioms block_13
theorem block_14 : check 896 = true := by decide
#print axioms block_14
theorem block_15 : check 960 = true := by decide
#print axioms block_15
theorem block_16 : check 1024 = true := by decide
#print axioms block_16
theorem block_17 : check 1088 = true := by decide
#print axioms block_17
theorem block_18 : check 1152 = true := by decide
#print axioms block_18
theorem block_19 : check 1216 = true := by decide
#print axioms block_19
theorem block_20 : check 1280 = true := by decide
#print axioms block_20
theorem block_21 : check 1344 = true := by decide
#print axioms block_21
theorem block_22 : check 1408 = true := by decide
#print axioms block_22
theorem block_23 : check 1472 = true := by decide
#print axioms block_23
theorem block_24 : check 1536 = true := by decide
#print axioms block_24
theorem block_25 : check 1600 = true := by decide
#print axioms block_25
theorem block_26 : check 1664 = true := by decide
#print axioms block_26
theorem block_27 : check 1728 = true := by decide
#print axioms block_27
theorem block_28 : check 1792 = true := by decide
#print axioms block_28
theorem block_29 : check 1856 = true := by decide
#print axioms block_29
theorem block_30 : check 1920 = true := by decide
#print axioms block_30
theorem block_31 : check 1984 = true := by decide
#print axioms block_31
theorem block_32 : check 2048 = true := by decide
#print axioms block_32
theorem block_33 : check 2112 = true := by decide
#print axioms block_33
theorem block_34 : check 2176 = true := by decide
#print axioms block_34
theorem block_35 : check 2240 = true := by decide
#print axioms block_35
theorem block_36 : check 2304 = true := by decide
#print axioms block_36
theorem block_37 : check 2368 = true := by decide
#print axioms block_37
theorem block_38 : check 2432 = true := by decide
#print axioms block_38
theorem block_39 : check 2496 = true := by decide
#print axioms block_39
theorem block_40 : check 2560 = true := by decide
#print axioms block_40
theorem block_41 : check 2624 = true := by decide
#print axioms block_41
theorem block_42 : check 2688 = true := by decide
#print axioms block_42
theorem block_43 : check 2752 = true := by decide
#print axioms block_43
theorem block_44 : check 2816 = true := by decide
#print axioms block_44
theorem block_45 : check 2880 = true := by decide
#print axioms block_45
theorem block_46 : check 2944 = true := by decide
#print axioms block_46
theorem block_47 : check 3008 = true := by decide
#print axioms block_47
theorem block_48 : check 3072 = true := by decide
#print axioms block_48
theorem block_49 : check 3136 = true := by decide
#print axioms block_49
theorem block_50 : check 3200 = true := by decide
#print axioms block_50
theorem block_51 : check 3264 = true := by decide
#print axioms block_51
theorem block_52 : check 3328 = true := by decide
#print axioms block_52
theorem block_53 : check 3392 = true := by decide
#print axioms block_53
theorem block_54 : check 3456 = true := by decide
#print axioms block_54
theorem block_55 : check 3520 = true := by decide
#print axioms block_55
theorem block_56 : check 3584 = true := by decide
#print axioms block_56
theorem block_57 : check 3648 = true := by decide
#print axioms block_57
theorem block_58 : check 3712 = true := by decide
#print axioms block_58
theorem block_59 : check 3776 = true := by decide
#print axioms block_59
theorem block_60 : check 3840 = true := by decide
#print axioms block_60
theorem block_61 : check 3904 = true := by decide
#print axioms block_61
theorem block_62 : check 3968 = true := by decide
#print axioms block_62
theorem block_63 : check 4032 = true := by decide
#print axioms block_63
theorem shear_bit (a b c : Bool) : ((a != c) && b) = ((a && b) != (c && b)) := by cases a <;> cases b <;> cases c <;> decide
theorem target_arithmetic : 333 * (99 - 97) = 666 := by decide
#print axioms shear_bit
#print axioms target_arithmetic
end NormPencilAudit
