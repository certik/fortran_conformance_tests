! rule: S10.1.4-001
! covers: binary-intrinsic-both-operand-values
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_binary_intrinsic_both_operand_values
  implicit none
  integer :: checks
  integer :: left, right, forward, reverse
  checks=0
  left = 19
  right = 6
  ! 19-6=13 and 6-19=-13; both operand values and order matter.
  forward = left - right
  reverse = right - left
  if (forward /= 13) then
    write(*,'(a)') 'EOP:binary_intrinsic_both_operand_values:left-minus-right'
    error stop
  end if
  checks=checks+1
  if (reverse /= -13) then
    write(*,'(a)') 'EOP:binary_intrinsic_both_operand_values:right-minus-left'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:binary_intrinsic_both_operand_values:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS BINARY INTRINSIC BOTH OPERAND VALUES OK'
end program evaluation_operations_binary_intrinsic_both_operand_values
