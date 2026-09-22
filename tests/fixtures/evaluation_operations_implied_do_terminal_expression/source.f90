! rule: S10.1.4-003
! covers: implied-do-terminal-expression
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_implied_do_terminal_expression
  implicit none
  integer :: checks
  integer :: i
  integer :: result(4)
  checks=0
  result = [(i, i=1, 2+2)]
  ! The terminal expression is 4, giving [1,2,3,4].
  if (any(result /= [1,2,3,4])) then
    write(*,'(a)') 'EOP:implied_do_terminal_expression:terminal-values'
    error stop
  end if
  checks=checks+1
  if (size(result) /= 4) then
    write(*,'(a)') 'EOP:implied_do_terminal_expression:terminal-size'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:implied_do_terminal_expression:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS IMPLIED DO TERMINAL EXPRESSION OK'
end program evaluation_operations_implied_do_terminal_expression
