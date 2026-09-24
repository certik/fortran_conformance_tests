! rule: S16.9.10-004
! covers: result-real-type
! covers: result-same-kind-as-z
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_aimag_result_characteristics
  implicit none
  integer :: checks
  integer, parameter :: rk = selected_real_kind(10)
  complex(kind=rk) :: z
  real(kind=rk) :: y
  interface type_code
    procedure real_code
    procedure complex_code
  end interface
  checks=0
  z = cmplx(2.0_rk, -3.0_rk, kind=rk)
  y = aimag(z)
  if (type_code(aimag(z)) /= 11) then
    write(*,'(a)') 'I16A:aimag_result_characteristics:real-type-resolution'
    error stop
  end if
  checks=checks+1
  if (kind(aimag(z)) /= rk) then
    write(*,'(a)') 'I16A:aimag_result_characteristics:same-kind'
    error stop
  end if
  checks=checks+1
  if (y /= -3.0_rk) then
    write(*,'(a)') 'I16A:aimag_result_characteristics:real-assignment-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'I16A:aimag_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A AIMAG RESULT CHARACTERISTICS OK'
contains
  integer function real_code(x)
    real(kind=rk), intent(in) :: x
    real_code = 11
  end function real_code
  integer function complex_code(x)
    complex(kind=rk), intent(in) :: x
    complex_code = 29
  end function complex_code
end program intrinsics_16_9_a_aimag_result_characteristics
