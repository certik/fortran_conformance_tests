program expr_r1007_missing_add_rhs_control
  implicit none
  integer :: x
  x = 1+2
  if (x /= 3) error stop 'R1007:control'
  write(*,'(a)') 'EXPRESSIONS R1007 MISSING RHS CONTROL OK'
end program expr_r1007_missing_add_rhs_control
