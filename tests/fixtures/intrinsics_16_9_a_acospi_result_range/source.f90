! rule: S16.9.7-004
! covers: acospi-result-half-revolutions-range
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acospi_result_range
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk), parameter :: x = 0.25_rk
  real(kind=rk) :: y
  checks=0
  y = acospi(x)
  if (.not. (y >= 0.0_rk .and. y <= 1.0_rk)) then
    write(*,'(a)') 'I16A:acospi_result_range:source-range'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:acospi_result_range:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSPI RESULT RANGE OK'
end program intrinsics_16_9_a_acospi_result_range
