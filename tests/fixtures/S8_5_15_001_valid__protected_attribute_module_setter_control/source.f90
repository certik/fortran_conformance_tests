module protected_attribute_setter_m
  implicit none
  integer, protected :: x = -11
contains
  subroutine set_x(v)
    integer, intent(in) :: v
    x = v
  end subroutine
end module
program main
  use protected_attribute_setter_m, only: x, set_x
  implicit none
  call set_x(17)
  if (x /= 17) error stop 1
  call set_x(29)
  if (x /= 29) error stop 2
  write(*,'(a)') 'PROTECTED ATTRIBUTE MODULE SETTER CONTROL OK'
end program
