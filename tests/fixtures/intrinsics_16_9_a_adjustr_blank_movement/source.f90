! rule: S16.9.9-005
! covers: trailing-blanks-deleted
! covers: leading-blanks-inserted
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_adjustr_blank_movement
  implicit none
  integer :: checks
  character(len=5) :: s, r
  checks=0
  s = 'AB#  '
  r = adjustr(s)
  if (len(r) /= 5) then
    write(*,'(a)') 'I16A:adjustr_blank_movement:result-length-before-equality'
    error stop
  end if
  checks=checks+1
  if (verify(r, ' ', back=.true.) /= 5) then
    write(*,'(a)') 'I16A:adjustr_blank_movement:trailing-last-nonblank'
    error stop
  end if
  checks=checks+1
  if (r(1:2) /= '  ') then
    write(*,'(a)') 'I16A:adjustr_blank_movement:leading-two-blanks'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'I16A:adjustr_blank_movement:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ADJUSTR BLANK MOVEMENT OK'
end program intrinsics_16_9_a_adjustr_blank_movement
