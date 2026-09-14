! rule: S6.3.2.2-003
! covers: keyword-named-constant
! evidence: effect
program separator_named_constant
  implicit none
  integer, parameter :: code = 0
  stopcode ! {error S6.3.2.2-003}
end program
