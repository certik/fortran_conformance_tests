! rule: S6.3.2.4-001
! covers: next-noncomment intervening-comments comment-ampersand marker-elision
! evidence: effect
program continuation_comments
  implicit none
  integer :: value
  value = -1
  value = 1 + & ! + 90 &
  ! 99 &

    2
  if (value /= 3) error stop 1
  value = 5 ! This ampersand does not continue the comment: &
  value = value + 1
  if (value /= 6) error stop 2
  value = 4 + &
    &5
  if (value /= 9) error stop 3
end program
