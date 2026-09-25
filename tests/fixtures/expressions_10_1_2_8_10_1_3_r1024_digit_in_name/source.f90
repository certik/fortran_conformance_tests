module expr_r1024_digit_in_name_mod
  implicit none
  interface operator(.ba.)
    module procedure ba_i
  end interface
contains
  pure integer function ba_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    ba_i = 10*lhs + rhs
  end function ba_i
end module expr_r1024_digit_in_name_mod
program expr_r1024_digit_in_name
  use expr_r1024_digit_in_name_mod
  implicit none
  integer :: x
  x = 1 .b1. 2
  print *, x
end program expr_r1024_digit_in_name
