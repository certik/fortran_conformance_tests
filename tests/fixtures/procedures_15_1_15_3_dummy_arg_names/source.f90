! rule: S15.1-003
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module dummy_arg_names_m
  implicit none
contains
  subroutine scale(x)
    integer, intent(inout) :: x
    x = x * 2
  end subroutine
  integer function twice(y)
    integer, intent(in) :: y
    twice = y * 2
  end function
end module
program dummy_arg_names
  use dummy_arg_names_m
  implicit none
  integer :: actual, result
  actual = 21
  call scale(actual)
  if (actual /= 42) error stop 1
  result = -777
  result = twice(21)
  if (result /= 42) error stop 2
  print '(a)', 'PROCEDURES 15.1 DUMMY ARG NAMES OK'
end program
