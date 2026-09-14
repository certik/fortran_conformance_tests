! rule: S6.3.2.4-003
! covers: terminal-marker marker-before-comment leading-marker no-leading-marker later-line-control
! evidence: positive-control
program noncharacter_positions
  implicit none
  integer :: value
  value = -1
  value = 1 + &
    2
  if (value /= 3) error stop 1
  value = 2 + & ! comment after the marker
    &3
  if (value /= 5) error stop 2
end program
