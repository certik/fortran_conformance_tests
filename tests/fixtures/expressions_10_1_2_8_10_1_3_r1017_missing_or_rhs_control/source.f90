program expr_r1017_missing_or_rhs_control
  implicit none
  logical :: ok
  ok = .false. .or. .true.
  if (.not. ok) error stop 'R1017:missing-or-control'
  write(*,'(a)') 'EXPRESSIONS R1017 MISSING OR RHS CONTROL OK'
end program expr_r1017_missing_or_rhs_control
