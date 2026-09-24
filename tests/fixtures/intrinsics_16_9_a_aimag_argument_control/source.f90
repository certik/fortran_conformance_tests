! rule: S16.9.10-003
! covers: z-complex-argument
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_aimag_argument_control
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  complex(kind=rk) :: z
  real(kind=rk) :: y
  checks=0
  z = cmplx(2.0_rk, -3.0_rk, kind=rk)
  y = aimag(z)
  if (y /= -3.0_rk) then
    write(*,'(a)') 'I16A:aimag_argument_control:complex-argument-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:aimag_argument_control:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A AIMAG ARGUMENT CONTROL OK'
end program intrinsics_16_9_a_aimag_argument_control
