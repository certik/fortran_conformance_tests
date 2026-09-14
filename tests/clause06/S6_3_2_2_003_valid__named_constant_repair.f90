! rule: S6.3.2.2-003
! covers: keyword-named-constant
! evidence: positive-control
program separator_named_constant
  implicit none
  integer, parameter :: code = 0
  stop code
end program
