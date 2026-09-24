module expr_defined_unary_m
  implicit none
  interface operator(.u.)
    module procedure u
  end interface
  interface operator(.inverse.)
    module procedure inverse
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = 10*x
  end function u
  integer function inverse(x)
    integer, intent(in) :: x
    inverse = 100 + x
  end function inverse
end module expr_defined_unary_m
program expr_r1003_forms
  use expr_defined_unary_m
  implicit none
  integer :: checks, x
  checks=0
  x = 6
  if (x /= 6) error stop 'ER1003:primary'
  checks=checks+1
  x = .u. 6
  if (x /= 60) error stop 'ER1003:defined'
  checks=checks+1
  if (checks /= 2) error stop 'ER1003:checks'
  write(*,'(a)') 'EXPRESSIONS R1003 FORMS OK'
end program expr_r1003_forms
