module expr_r1023_missing_rhs_control_mod
  implicit none
  interface operator(.join.)
    module procedure join_i
  end interface
contains
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
end module expr_r1023_missing_rhs_control_mod
program expr_r1023_missing_level5_rhs_control
  use expr_r1023_missing_rhs_control_mod
  implicit none
  integer :: x
  x = 1 .join. 2
  if (x /= 12) error stop 'R1023:missing-rhs-control'
  write(*,'(a)') 'EXPRESSIONS R1023 MISSING RHS CONTROL OK'
end program expr_r1023_missing_level5_rhs_control
