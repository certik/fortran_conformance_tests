module protected_attribute_readonly_m
  implicit none
  integer, protected :: x = 41
  integer, protected :: z = 13
end module
program main
  use protected_attribute_readonly_m, only: x, y => z
  implicit none
  integer :: observed
  observed = x + y
  if (observed /= 54) error stop 1
  call take_in(x)
  write(*,'(a)') 'PROTECTED ATTRIBUTE READONLY USE OK'
contains
  subroutine take_in(v)
    integer, intent(in) :: v
    if (v /= 41) error stop 2
  end subroutine
end program
