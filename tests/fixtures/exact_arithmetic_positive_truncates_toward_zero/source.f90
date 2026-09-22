! rule: S10.1.5.2.2-001
! covers: positive-truncates-toward-zero
! Oracle constants are hand-computed integer literals from Fortran 2023 10.1.5.2.2.
program exact_arithmetic_positive_truncates_toward_zero
  implicit none
  integer :: checks, result
  checks=0
  ! 8/3 has mathematical quotient 2.666..., so the closest integer between 0 and 2.666... is 2.
  result = 8 / 3
  if (result /= 2) then
    write(*,'(a)') 'EAF:positive_truncates_toward_zero:positive-eight-over-three'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'EAF:positive_truncates_toward_zero:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC POSITIVE TRUNCATES TOWARD ZERO OK'
end program exact_arithmetic_positive_truncates_toward_zero
