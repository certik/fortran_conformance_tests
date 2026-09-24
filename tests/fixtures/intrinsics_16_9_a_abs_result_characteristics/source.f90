! rule: S16.9.2-002
! covers: abs-integer-result-characteristics
! covers: abs-real-result-characteristics
! covers: abs-complex-result-real-characteristics
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_abs_result_characteristics
  implicit none
  integer :: checks
  integer, parameter :: ik = selected_int_kind(18)
  integer, parameter :: rk = selected_real_kind(10)
  integer(kind=ik) :: i
  real(kind=rk) :: x, cabs
  complex(kind=rk) :: z
  checks=0
  i = -7_ik
  x = -2.0_rk
  z = cmplx(0.0_rk, -2.0_rk, kind=rk)
  if (kind(abs(i)) /= ik) then
    write(*,'(a)') 'I16A:abs_result_characteristics:integer-kind'
    error stop
  end if
  checks=checks+1
  if (kind(abs(x)) /= rk) then
    write(*,'(a)') 'I16A:abs_result_characteristics:real-kind'
    error stop
  end if
  checks=checks+1
  if (kind(abs(z)) /= rk) then
    write(*,'(a)') 'I16A:abs_result_characteristics:complex-result-kind'
    error stop
  end if
  checks=checks+1
  cabs = abs(z)
  if (.not. (cabs >= 0.0_rk)) then
    write(*,'(a)') 'I16A:abs_result_characteristics:complex-real-assignment'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'I16A:abs_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ABS RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_abs_result_characteristics
