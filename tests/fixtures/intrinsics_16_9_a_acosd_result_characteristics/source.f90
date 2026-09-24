! rule: S16.9.5-002
! covers: acosd-result-characteristics-same-as-x
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acosd_result_characteristics
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk) :: x, y
  checks=0
  x = 0.25_rk
  if (kind(acosd(x)) /= rk) then
    write(*,'(a)') 'I16A:acosd_result_characteristics:result-kind'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:acosd_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSD RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_acosd_result_characteristics
