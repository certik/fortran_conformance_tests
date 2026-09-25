program main
  implicit none
  integer :: x, y
  volatile x
  x = 8
  y = 13
  if (x /= 8) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VOLATILE MISSING LIST CONTROL OK'
end program
