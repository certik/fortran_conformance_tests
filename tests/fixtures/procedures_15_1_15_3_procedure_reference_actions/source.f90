! rule: S15.1-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module procedure_reference_actions_m
  implicit none
contains
  subroutine set_answer(x)
    integer, intent(out) :: x
    x = 42
  end subroutine
  subroutine leave_sentinel(x)
    integer, intent(inout) :: x
    x = x
  end subroutine
end module
program procedure_reference_actions
  use procedure_reference_actions_m
  implicit none
  integer :: actual
  actual = -333
  call set_answer(actual)
  if (actual /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.1 PROCEDURE REFERENCE ACTIONS OK'
end program
