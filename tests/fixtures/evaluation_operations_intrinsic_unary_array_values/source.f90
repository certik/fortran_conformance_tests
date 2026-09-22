! rule: S10.1.4-005
! covers: intrinsic-unary-array-values
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_intrinsic_unary_array_values
  implicit none
  integer :: checks
  integer :: a(3), result(3)
  checks=0
  a = [1,-2,3]
  ! Elementwise unary minus gives [-1,2,-3].
  result = -a
  if (any(result /= [-1,2,-3])) then
    write(*,'(a)') 'EOP:intrinsic_unary_array_values:unary-array-values'
    error stop
  end if
  checks=checks+1
  if (sum(result) /= -2) then
    write(*,'(a)') 'EOP:intrinsic_unary_array_values:unary-array-sum'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:intrinsic_unary_array_values:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS INTRINSIC UNARY ARRAY VALUES OK'
end program evaluation_operations_intrinsic_unary_array_values
