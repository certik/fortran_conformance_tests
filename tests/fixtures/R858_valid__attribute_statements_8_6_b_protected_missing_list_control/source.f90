module attribute_statements_protected_data_m
  implicit none
  integer :: x = 19
  integer :: y = 23
  protected :: x
contains
  subroutine set_values(a, b)
    integer, intent(in) :: a, b
    x = a
    y = b
  end subroutine
end module
program main
  use attribute_statements_protected_data_m, only: x, y, set_values
  implicit none
  call set_values(31, 37)
  if (x /= 31) error stop 1
  if (y /= 37) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS PROTECTED MISSING LIST CONTROL OK'
end program
