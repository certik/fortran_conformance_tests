! rule: S6.3.2.2-002
! covers: character-context-exclusion
! evidence: effect
program blank_runs_character
  implicit none
  character(len=*), parameter :: doubled = 'a  b', single = 'a b'
  character(len=4) :: rendered
  if (len(doubled) /= 4) stop 1
  if (len(single) /= 3) stop 2
  if (doubled == single) stop 3
  if (doubled(2:3) /= '  ') stop 4
  write(rendered, 100)
100 format('a  b')
  if (rendered /= doubled) stop 5
end program
