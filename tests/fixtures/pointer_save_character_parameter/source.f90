program pointer_character_parameter
  implicit none
  character(:), pointer :: p
  character(len=2), target :: short, raw
  character(len=5), target :: long
  integer :: checks
  checks = 0
  short = 'ab'
  long = 'pqrst'
  p => short
  if (len(p) /= 2) error stop
  checks = checks + 1
  if (p /= 'ab') error stop
  checks = checks + 1
  p => long
  if (len(p) /= 5) error stop
  checks = checks + 1
  if (p /= 'pqrst') error stop
  checks = checks + 1
  p => raw
  if (len(p) /= 2) error stop
  checks = checks + 1
  p = 'xy'
  if (raw /= 'xy') error stop
  checks = checks + 1
  if (checks /= 6) error stop
  print '(a)', 'POINTER CHARACTER PARAMETER OK'
end program pointer_character_parameter
