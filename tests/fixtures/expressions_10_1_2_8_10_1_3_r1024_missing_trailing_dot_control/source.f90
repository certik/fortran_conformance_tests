module expr_r1024_missing_trailing_dot_control_mod
  implicit none
  interface operator(.b.)
    module procedure b_i
  end interface
contains
  pure integer function b_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    b_i = 10*lhs + rhs
  end function b_i
end module expr_r1024_missing_trailing_dot_control_mod
program expr_r1024_missing_trailing_dot_control
  use expr_r1024_missing_trailing_dot_control_mod
  implicit none
  integer :: x
  x = 1 .b. 2
  if (x /= 12) error stop 'R1024:missing-trailing-dot-rejected'
  write(*,'(a)') 'EXPRESSIONS R1024 MISSING-TRAILING-DOT-REJECTED CONTROL OK'
end program expr_r1024_missing_trailing_dot_control
