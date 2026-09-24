program expr_r1013_relation_chain_control
  implicit none
  logical :: ok
  ok = 1 < 2
  if (.not. ok) error stop 'R1013:chain-control'
  write(*,'(a)') 'EXPRESSIONS R1013 CHAIN CONTROL OK'
end program expr_r1013_relation_chain_control
