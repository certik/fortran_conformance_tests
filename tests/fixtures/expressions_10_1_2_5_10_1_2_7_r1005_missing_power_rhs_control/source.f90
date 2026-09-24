program expr_r1005_missing_power_rhs_control
  implicit none
  integer :: x
  x = 2**3
  if (x /= 8) error stop 'R1005:control'
  write(*,'(a)') 'EXPRESSIONS R1005 MISSING RHS CONTROL OK'
end program expr_r1005_missing_power_rhs_control
