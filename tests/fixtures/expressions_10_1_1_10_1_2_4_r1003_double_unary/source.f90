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
program expr_r1003_double_unary
  use expr_defined_unary_m
  implicit none
  integer :: x
  x = 3
  x = .u. .inverse. x
end program expr_r1003_double_unary
