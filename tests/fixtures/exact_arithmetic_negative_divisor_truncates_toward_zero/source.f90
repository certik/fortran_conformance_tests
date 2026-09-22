! rule: S10.1.5.2.2-001
! covers: negative-divisor-truncates-toward-zero
! Oracle constants are hand-computed integer literals from Fortran 2023 10.1.5.2.2.
program exact_arithmetic_negative_divisor_truncates_toward_zero
  implicit none
  integer :: checks, result
  checks=0
  ! 8/(-3) has mathematical quotient -2.666..., so the closest integer between 0 and -2.666... is -2.
  ! Flooring division would give -3; this fixture distinguishes truncation toward zero from floor.
  result = 8 / (-3)
  if (result /= -2) then
    write(*,'(a)') 'EAF:negative_divisor_truncates_toward_zero:negative-divisor-eight-over-three'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'EAF:negative_divisor_truncates_toward_zero:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC NEGATIVE DIVISOR TRUNCATES TOWARD ZERO OK'
end program exact_arithmetic_negative_divisor_truncates_toward_zero
