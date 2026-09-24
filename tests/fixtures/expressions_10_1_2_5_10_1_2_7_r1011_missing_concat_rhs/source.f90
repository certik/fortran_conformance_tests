program expr_r1011_missing_concat_rhs
  implicit none
  character(len=2) :: s
  s = 'a'//
  print *, s
end program expr_r1011_missing_concat_rhs
