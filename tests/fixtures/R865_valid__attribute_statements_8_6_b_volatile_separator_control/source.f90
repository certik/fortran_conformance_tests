program main
  implicit none
  integer :: x, y
  volatile :: x, y
  x = 8
  y = 13
  if (x + y /= 21) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VOLATILE SEPARATOR CONTROL OK'
end program
