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
program expr_level1_precedence
  use expr_defined_unary_m
  implicit none
  integer :: checks, x
  checks=0
  x = .u. 2 * 3
  if (x /= 60) error stop 'EL1:precedence'
  checks=checks+1
  x = .u.(1+2)
  if (x /= 30) error stop 'EL1:parenthesized'
  checks=checks+1
  x = 6 * 2
  if (x /= 12) error stop 'EL1:primary-only'
  checks=checks+1
  if (checks /= 3) error stop 'EL1:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL1 PRECEDENCE OK'
end program expr_level1_precedence
