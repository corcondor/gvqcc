import Init
namespace GVQCC.V79
theorem conditionalSpan (f a b : Bool) :
    (f && Bool.xor a b) = Bool.xor (f && a) (f && b) := by
  cases f <;> cases a <;> cases b <;> decide
theorem siblingTransition (f b : Bool) :
    Bool.xor f (f && b) = (f && !b) := by
  cases f <;> cases b <;> decide
theorem complementaryChildren (f b : Bool) :
    Bool.xor (f && b) (f && !b) = f := by
  cases f <;> cases b <;> decide
theorem nestedProduct (f a b : Bool) :
    ((f && a) && (f && b)) = (f && (a && b)) := by
  cases f <;> cases a <;> cases b <;> decide
def bitI (x : Bool) : Int := if x then 1 else 0
theorem phaseEcho (s g : Bool) :
    bitI (Bool.xor s g) - bitI s = (1 - 2 * bitI s) * bitI g := by
  cases s <;> cases g <;> decide
end GVQCC.V79
