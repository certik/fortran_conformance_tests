program expr_r1018_missing_equiv_rhs_control
  implicit none
  logical :: ok
  ok = .true. .eqv. .false.
  if (ok) error stop 'R1018:missing-equiv-control'
  write(*,'(a)') 'EXPRESSIONS R1018 MISSING EQUIV RHS CONTROL OK'
end program expr_r1018_missing_equiv_rhs_control
