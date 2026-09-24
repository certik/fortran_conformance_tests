! rule: S16.9.4-004
! covers: acos-real-result-radians-range
! covers: acos-complex-real-part-radians-range
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acos_result_ranges
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk) :: x, rr
  complex(kind=rk) :: z, rz
  checks=0
  x = 0.25_rk
  z = cmplx(0.25_rk, 0.5_rk, kind=rk)
  rr = acos(x)
  if (.not. (rr >= 0.0_rk .and. rr <= 4.0_rk)) then
    write(*,'(a)') 'I16A:acos_result_ranges:real-radians-range'
    error stop
  end if
  checks=checks+1
  rz = acos(z)
  if (.not. (real(rz) >= 0.0_rk .and. real(rz) <= 4.0_rk)) then
    write(*,'(a)') 'I16A:acos_result_ranges:complex-real-part-range'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:acos_result_ranges:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOS RESULT RANGES OK'
end program intrinsics_16_9_a_acos_result_ranges
