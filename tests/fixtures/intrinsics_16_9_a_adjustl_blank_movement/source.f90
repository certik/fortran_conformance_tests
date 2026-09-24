! rule: S16.9.8-005
! covers: leading-blanks-deleted
! covers: trailing-blanks-inserted
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_adjustl_blank_movement
  implicit none
  integer :: checks
  character(len=5) :: s, r
  checks=0
  s = '  AB#'
  r = adjustl(s)
  if (len(r) /= 5) then
    write(*,'(a)') 'I16A:adjustl_blank_movement:result-length-before-equality'
    error stop
  end if
  checks=checks+1
  if (verify(r, ' ') /= 1) then
    write(*,'(a)') 'I16A:adjustl_blank_movement:leading-first-nonblank'
    error stop
  end if
  checks=checks+1
  if (r(4:5) /= '  ') then
    write(*,'(a)') 'I16A:adjustl_blank_movement:trailing-two-blanks'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'I16A:adjustl_blank_movement:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ADJUSTL BLANK MOVEMENT OK'
end program intrinsics_16_9_a_adjustl_blank_movement
