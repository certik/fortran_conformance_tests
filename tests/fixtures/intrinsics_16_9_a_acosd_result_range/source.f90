! rule: S16.9.5-004
! covers: acosd-result-degrees-range
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acosd_result_range
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk) :: x, y
  checks=0
  x = 0.25_rk
  y = acosd(x)
  if (.not. (y >= 0.0_rk .and. y <= 180.0_rk)) then
    write(*,'(a)') 'I16A:acosd_result_range:source-range'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:acosd_result_range:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSD RESULT RANGE OK'
end program intrinsics_16_9_a_acosd_result_range
