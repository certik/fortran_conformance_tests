! rule: S16.9.2-001
! covers: abs-argument-integer-real-or-complex
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_abs_argument_control
  implicit none
  integer :: checks
  integer :: iv
  real :: rv, cv
  checks=0
  iv = abs(-7)
  rv = abs(-2.0)
  cv = abs(cmplx(0.0,-3.0))
  if (.not. (iv == 7 .and. rv == 2.0 .and. cv > 0.0)) then
    write(*,'(a)') 'I16A:abs_argument_control:all-admissible-forms'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:abs_argument_control:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ABS ARGUMENT CONTROL OK'
end program intrinsics_16_9_a_abs_argument_control
