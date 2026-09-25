program expr_r1016_missing_and_rhs_control
  implicit none
  logical :: ok
  ok = .true. .and. .false.
  if (ok) error stop 'R1016:missing-and-control'
  write(*,'(a)') 'EXPRESSIONS R1016 MISSING AND RHS CONTROL OK'
end program expr_r1016_missing_and_rhs_control
