! rule: S16.9.6-002
! covers: acosh-result-characteristics-same-as-x
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acosh_result_characteristics
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk) :: x
  complex(kind=rk) :: z
  checks=0
  x = 2.0_rk
  z = cmplx(0.25_rk, 0.5_rk, kind=rk)
  if (kind(acosh(x)) /= rk) then
    write(*,'(a)') 'I16A:acosh_result_characteristics:real-result-kind'
    error stop
  end if
  checks=checks+1
  if (kind(acosh(z)) /= rk) then
    write(*,'(a)') 'I16A:acosh_result_characteristics:complex-result-kind'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:acosh_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSH RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_acosh_result_characteristics
