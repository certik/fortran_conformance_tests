! rule: S10.1.4-004
! covers: same-shape-array-operands
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_same_shape_array_operands
  implicit none
  integer :: checks
  integer :: a(3), b(3), result(3)
  checks=0
  a = [1,2,3]
  b = [10,20,30]
  ! Corresponding sums are [1+10,2+20,3+30] = [11,22,33].
  result = a + b
  if (any(result /= [11,22,33])) then
    write(*,'(a)') 'EOP:same_shape_array_operands:same-shape-values'
    error stop
  end if
  checks=checks+1
  if (sum(result) /= 66) then
    write(*,'(a)') 'EOP:same_shape_array_operands:same-shape-sum'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:same_shape_array_operands:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS SAME SHAPE ARRAY OPERANDS OK'
end program evaluation_operations_same_shape_array_operands
