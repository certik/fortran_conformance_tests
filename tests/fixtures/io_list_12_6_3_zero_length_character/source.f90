program io_list_zero_length_character
  implicit none
  integer :: checks
  character(len=1) :: out, z
  checks = 0
  z = 'X'
  out = '#'
  write(out,'(A,I1)') z(:0), 7
  if (len(z(:0)) /= 0) error stop 'zero character len'
  checks = checks + 1
  if (out /= '7') error stop 'zero character effective item'
  checks = checks + 1
  if (checks /= 2) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 ZERO_LENGTH_CHARACTER OK'
end program io_list_zero_length_character
