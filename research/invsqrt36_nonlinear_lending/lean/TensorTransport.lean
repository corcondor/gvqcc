namespace GVQCCTensorTransport

theorem delta_transport (old next : Bool) :
    Bool.xor old (Bool.xor old next) = next := by
  cases old <;> cases next <;> decide

theorem shared_factor (a b p : Bool) :
    Bool.xor (a && p) (b && p) = (Bool.xor a b && p) := by
  cases a <;> cases b <;> cases p <;> decide

theorem phase_correction (m a b : Bool) :
    Bool.xor (m && Bool.xor a b) (Bool.xor (m && a) (m && b)) = false := by
  cases m <;> cases a <;> cases b <;> decide

theorem three_stage_transport (a b c : Bool) :
    Bool.xor (Bool.xor a (Bool.xor a b)) (Bool.xor b c) = c := by
  cases a <;> cases b <;> cases c <;> decide

end GVQCCTensorTransport
