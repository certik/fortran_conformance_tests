program data_statement_c886_repeat_bounds
  implicit none
  integer, parameter :: n = 2
  integer :: repeated(2), tail
  data repeated, tail /n*61, 0*999, 67/
  if (repeated(1) /= 61) error stop 1
  if (repeated(2) /= 61) error stop 2
  if (tail /= 67) error stop 3
  write(*,'(a)') 'DATA STATEMENT C886 REPEAT BOUNDS OK'
end program data_statement_c886_repeat_bounds
