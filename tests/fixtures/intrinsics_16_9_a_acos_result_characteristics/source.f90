! rule: S16.9.4-002
! covers: acos-result-characteristics-same-as-x
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acos_result_characteristics
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk) :: x
  complex(kind=rk) :: z
  checks=0
  x = 0.25_rk
  z = cmplx(0.25_rk, 0.5_rk, kind=rk)
  if (kind(acos(x)) /= rk) then
    write(*,'(a)') 'I16A:acos_result_characteristics:real-result-kind'
    error stop
  end if
  checks=checks+1
  if (kind(acos(z)) /= rk) then
    write(*,'(a)') 'I16A:acos_result_characteristics:complex-result-kind'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:acos_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOS RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_acos_result_characteristics
