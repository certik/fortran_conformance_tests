! rule: S10.1.5.2.2-001
! covers: exact-integer-division
! Oracle constants are hand-computed integer literals from Fortran 2023 10.1.5.2.2.
program exact_arithmetic_exact_integer_division
  implicit none
  integer :: checks, result
  checks=0
  ! 8/4 has mathematical quotient exactly 2, already an integer between 0 and 2.
  result = 8 / 4
  if (result /= 2) then
    write(*,'(a)') 'EAF:exact_integer_division:exact-eight-over-four'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'EAF:exact_integer_division:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC EXACT INTEGER DIVISION OK'
end program exact_arithmetic_exact_integer_division
