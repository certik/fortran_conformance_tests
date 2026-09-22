! rule: S10.1.4-003
! covers: implied-do-stride-expression
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_implied_do_stride_expression
  implicit none
  integer :: checks
  integer :: i
  integer :: result(3)
  checks=0
  result = [(i, i=1, 5, 1+1)]
  ! The stride expression is 2, so the sequence is 1,3,5.
  if (any(result /= [1,3,5])) then
    write(*,'(a)') 'EOP:implied_do_stride_expression:stride-values'
    error stop
  end if
  checks=checks+1
  if (size(result) /= 3) then
    write(*,'(a)') 'EOP:implied_do_stride_expression:stride-size'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:implied_do_stride_expression:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS IMPLIED DO STRIDE EXPRESSION OK'
end program evaluation_operations_implied_do_stride_expression
