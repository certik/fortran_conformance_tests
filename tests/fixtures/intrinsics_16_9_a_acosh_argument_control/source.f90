! rule: S16.9.6-001
! covers: acosh-argument-admissible
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_acosh_argument_control
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  real(kind=rk) :: xr, rr
  complex(kind=rk) :: z, rz
  checks=0
  xr = 2.0_rk
  z = cmplx(0.25_rk, 0.5_rk, kind=rk)
  rr = acosh(xr)
  rz = acosh(z)
  if (.not. (real(rz) >= 0.0_rk .and. aimag(rz) >= -4.0_rk .and. aimag(rz) <= 4.0_rk)) then
    write(*,'(a)') 'I16A:acosh_argument_control:complex-argument-range'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:acosh_argument_control:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACOSH ARGUMENT CONTROL OK'
end program intrinsics_16_9_a_acosh_argument_control
