! rule: S10.1.4-003
! covers: implied-do-initial-expression
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_implied_do_initial_expression
  implicit none
  integer :: checks
  integer :: i
  integer :: result(3)
  checks=0
  result = [(i, i=1+1, 4)]
  ! The initial expression is 2, so the constructor is [2,3,4], not [1,2,3,4].
  if (any(result /= [2,3,4])) then
    write(*,'(a)') 'EOP:implied_do_initial_expression:initial-values'
    error stop
  end if
  checks=checks+1
  if (size(result) /= 3) then
    write(*,'(a)') 'EOP:implied_do_initial_expression:initial-size'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:implied_do_initial_expression:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS IMPLIED DO INITIAL EXPRESSION OK'
end program evaluation_operations_implied_do_initial_expression
