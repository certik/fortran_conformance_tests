module attribute_statements_value_double_m
  implicit none
contains
  subroutine bump(x, y)
    integer :: x, y
    value :: x, y
    x = x + 10
    y = y + 20
  end subroutine
end module
program main
  use attribute_statements_value_double_m
  implicit none
  integer :: a, b
  a = 3
  b = 4
  call bump(a, b)
  if (a /= 3) error stop 1
  if (b /= 4) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VALUE SEPARATOR CONTROL OK'
end program
