program expr_r1015_double_not_control
  implicit none
  logical :: ok
  ok = .not.(.not. .false.)
  if (ok) error stop 'R1015:double-not-control'
  write(*,'(a)') 'EXPRESSIONS R1015 DOUBLE NOT CONTROL OK'
end program expr_r1015_double_not_control
