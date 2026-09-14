! rule: S6.3.2.2-001
! covers: character-literal character-edit-descriptor format-specification
! evidence: positive-control
program blank_exceptions
  implicit none
  character(len=4) :: literal, rendered
  character(len=2) :: number
  literal = 'a  b'
  write(rendered, 100)
100 format('a  b')
  write(number, 200) 7
200 format(I 2)
  if (literal /= 'a' // '  ' // 'b') stop 1
  if (rendered /= literal) stop 2
  if (number /= ' 7') stop 3
end program
