program expr_r1011_missing_concat_rhs_control
  implicit none
  character(len=2) :: s
  s = 'a'//'b'
  if (len('a'//'b') /= 2) error stop 'R1011:control-len'
  if (s /= 'ab') error stop 'R1011:control-value'
  write(*,'(a)') 'EXPRESSIONS R1011 MISSING RHS CONTROL OK'
end program expr_r1011_missing_concat_rhs_control
