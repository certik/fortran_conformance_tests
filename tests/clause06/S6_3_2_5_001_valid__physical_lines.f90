! rule: S6.3.2.5-001
! covers: line-end comment-start continued-exception
! evidence: effect
program physical_termination
  implicit none
  integer :: left, right, joined
  left = -1
  right = -1
  joined = -1
  left = 7
  right = 11
  if (left /= 7) error stop 1
  if (right /= 11) error stop 2
  left = 13 ! ; right = 99
  if (left /= 13) error stop 3
  if (right /= 11) error stop 4
  joined = 1 + & ! The statement has not ended.
! The continuation resumes on the next noncomment line.
    2
  if (joined /= 3) error stop 5
end program
