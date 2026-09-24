! rule: S16.9.6-004
! covers: acosh-complex-real-part-nonnegative
! covers: acosh-complex-imaginary-part-radians-range
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acosh_complex_ranges
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  complex(kind=rk) :: z, r
  checks=0
  z = cmplx(0.25_rk, 0.5_rk, kind=rk)
  r = acosh(z)
  if (.not. (real(r) >= 0.0_rk)) then
    write(*,'(a)') 'I16A:acosh_complex_ranges:complex-real-nonnegative'
    error stop
  end if
  checks=checks+1
  if (.not. (aimag(r) >= -4.0_rk .and. aimag(r) <= 4.0_rk)) then
    write(*,'(a)') 'I16A:acosh_complex_ranges:complex-imag-range'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:acosh_complex_ranges:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSH COMPLEX RANGES OK'
end program intrinsics_16_9_a_acosh_complex_ranges
