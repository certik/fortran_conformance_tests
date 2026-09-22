! rule: S10.1.4-005
! covers: unary-result-same-shape
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_unary_result_same_shape
  implicit none
  integer :: checks
  integer :: a(2:3,-1:1), result(2:3,-1:1)
  checks=0
  a(2,-1) = -11
  a(3,-1) = 12
  a(2,0) = -21
  a(3,0) = 23
  a(2,1) = 31
  a(3,1) = -32
  ! The operand has extents 2 by 3; unary minus preserves result shape.
  result = -a
  if (any(shape(-a) /= [2,3])) then
    write(*,'(a)') 'EOP:unary_result_same_shape:unary-shape'
    error stop
  end if
  checks=checks+1
  if (result(2,-1) /= 11) then
    write(*,'(a)') 'EOP:unary_result_same_shape:unary-lower-corner'
    error stop
  end if
  checks=checks+1
  if (result(3,0) /= -23) then
    write(*,'(a)') 'EOP:unary_result_same_shape:unary-interior'
    error stop
  end if
  checks=checks+1
  if (result(3,1) /= 32) then
    write(*,'(a)') 'EOP:unary_result_same_shape:unary-upper-corner'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'EOP:unary_result_same_shape:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS UNARY RESULT SAME SHAPE OK'
end program evaluation_operations_unary_result_same_shape
