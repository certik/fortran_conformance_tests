! rule: S16.9.10-005
! covers: imaginary-component-value
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_aimag_imaginary_component
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  complex(kind=rk) :: z
  real(kind=rk) :: y
  checks=0
  z = cmplx(2.0_rk, -3.0_rk, kind=rk)
  y = aimag(z)
  if (y /= -3.0_rk) then
    write(*,'(a)') 'I16A:aimag_imaginary_component:imaginary-component'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:aimag_imaginary_component:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A AIMAG IMAGINARY COMPONENT OK'
end program intrinsics_16_9_a_aimag_imaginary_component
