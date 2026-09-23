program specification_expression_r1029_scalar
  implicit none
  integer :: a(2*3+1)
  if (size(a) /= 7) error stop 'SER1029:scalar'
  write(*,'(a)') 'SPECEXPR R1029 SCALAR OK'
end program specification_expression_r1029_scalar
