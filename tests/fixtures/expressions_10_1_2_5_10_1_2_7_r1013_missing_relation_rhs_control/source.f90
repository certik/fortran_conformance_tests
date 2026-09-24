program expr_r1013_missing_relation_rhs_control
  implicit none
  logical :: ok
  ok = 1 < 2
  if (.not. ok) error stop 'R1013:missing-rhs-control'
  write(*,'(a)') 'EXPRESSIONS R1013 MISSING RHS CONTROL OK'
end program expr_r1013_missing_relation_rhs_control
