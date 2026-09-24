! rule: S16.9.3-001
! covers: achar-i-argument-integer
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_achar_argument_control
  implicit none
  integer :: checks
  character(len=1) :: c
  checks=0
  c = achar(88)
  if (.not. (len(c) == 1 .and. c == 'X')) then
    write(*,'(a)') 'I16A:achar_argument_control:integer-i-argument'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'I16A:achar_argument_control:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACHAR ARGUMENT CONTROL OK'
end program intrinsics_16_9_a_achar_argument_control
