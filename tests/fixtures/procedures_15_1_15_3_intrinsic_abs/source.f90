! rule: S15.2.2.1-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
program intrinsic_abs
  implicit none
  intrinsic :: abs
  integer :: result
  result = -777
  result = abs(-42)
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.1 INTRINSIC ABS OK'
contains
  integer function user_abs(x)
    integer, intent(in) :: x
    user_abs = -999
  end function
end program
