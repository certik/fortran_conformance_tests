program main
  implicit none
  integer :: a(2)
  volatile :: a(1)
  a = [5, 6]
  if (a(1) + a(2) /= 11) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VOLATILE DESIGNATOR CONTROL OK'
end program
