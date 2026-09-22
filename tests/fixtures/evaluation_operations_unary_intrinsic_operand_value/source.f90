! rule: S10.1.4-001
! covers: unary-intrinsic-operand-value
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_unary_intrinsic_operand_value
  implicit none
  integer :: checks
  integer :: x, y, r1, r2
  checks=0
  x = -7
  y = 4
  ! -(-7)=7, and -(4)=-4; the second case rejects absolute-value behavior.
  r1 = -x
  r2 = -y
  if (r1 /= 7) then
    write(*,'(a)') 'EOP:unary_intrinsic_operand_value:minus-negative-seven'
    error stop
  end if
  checks=checks+1
  if (r2 /= -4) then
    write(*,'(a)') 'EOP:unary_intrinsic_operand_value:minus-positive-four'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:unary_intrinsic_operand_value:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS UNARY INTRINSIC OPERAND VALUE OK'
end program evaluation_operations_unary_intrinsic_operand_value
