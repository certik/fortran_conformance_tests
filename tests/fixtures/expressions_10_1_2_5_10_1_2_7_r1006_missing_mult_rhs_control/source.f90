program expr_r1006_missing_mult_rhs_control
  implicit none
  integer :: x
  x = 2*3
  if (x /= 6) error stop 'R1006:control'
  write(*,'(a)') 'EXPRESSIONS R1006 MISSING RHS CONTROL OK'
end program expr_r1006_missing_mult_rhs_control
