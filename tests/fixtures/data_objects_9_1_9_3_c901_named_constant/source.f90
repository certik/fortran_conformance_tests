! rule: C901
! covers: named-constant-excluded
! evidence: effect
! standard: f2023
! oracle-basis: standard
program dataobj_c901_named_constant
  implicit none
  integer, parameter :: k = 1
  k = 2
end program dataobj_c901_named_constant
