module expr_r1024_missing_leading_dot_mod
  implicit none
  interface operator(.b.)
    module procedure b_i
  end interface
contains
  pure integer function b_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    b_i = 10*lhs + rhs
  end function b_i
end module expr_r1024_missing_leading_dot_mod
program expr_r1024_missing_leading_dot
  use expr_r1024_missing_leading_dot_mod
  implicit none
  integer :: x
  x = 1 b. 2
  print *, x
end program expr_r1024_missing_leading_dot
