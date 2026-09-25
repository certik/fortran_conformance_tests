module attribute_statements_value_no_colon_m
  implicit none
contains
  subroutine bump(x)
    integer :: x
    value : x
    x = x + 10
  end subroutine
end module
program main
  use attribute_statements_value_no_colon_m
  implicit none
  integer :: a
  a = 3
  call bump(a)
  if (a /= 3) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VALUE SINGLE COLON CONTROL OK'
end program
