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
program expr_r1004_spelling
  use expr_defined_unary_m
  implicit none
  integer :: checks, x
  checks=0
  x = .u. 4
  if (x /= 40) error stop 'ER1004:single'
  checks=checks+1
  x = .inverse. 5
  if (x /= 105) error stop 'ER1004:multiple'
  checks=checks+1
  if (checks /= 2) error stop 'ER1004:checks'
  write(*,'(a)') 'EXPRESSIONS R1004 SPELLING OK'
end program expr_r1004_spelling
