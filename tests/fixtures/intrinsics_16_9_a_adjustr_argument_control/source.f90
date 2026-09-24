! rule: S16.9.9-003
! covers: string-character-argument
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_adjustr_argument_control
  implicit none
  integer :: checks
  character(len=5) :: s, r
  checks=0
  s = 'AB#  '
  r = adjustr(s)
  if (len(r) /= 5) then
    write(*,'(a)') 'I16A:adjustr_argument_control:result-length-before-equality'
    error stop
  end if
  checks=checks+1
  if (r /= '  AB#') then
    write(*,'(a)') 'I16A:adjustr_argument_control:character-argument-result'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:adjustr_argument_control:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ADJUSTR ARGUMENT CONTROL OK'
end program intrinsics_16_9_a_adjustr_argument_control
