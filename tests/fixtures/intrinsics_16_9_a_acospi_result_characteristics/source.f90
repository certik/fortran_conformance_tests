! rule: S16.9.7-002
! covers: acospi-result-characteristics-same-as-x
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acospi_result_characteristics
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk), parameter :: x = 0.25_rk
  real(kind=rk) :: y
  checks=0
  if (kind(acospi(x)) /= rk) then
    write(*,'(a)') 'I16A:acospi_result_characteristics:result-kind'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:acospi_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSPI RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_acospi_result_characteristics
