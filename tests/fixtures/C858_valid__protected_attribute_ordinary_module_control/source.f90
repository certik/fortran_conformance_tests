module protected_attribute_common_control_m
  implicit none
  integer, protected :: x = -9
contains
  subroutine set_x(v)
    integer, intent(in) :: v
    x = v
  end subroutine
end module
program main
  use protected_attribute_common_control_m, only: x, set_x
  implicit none
  call set_x(33)
  if (x /= 33) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE ORDINARY MODULE CONTROL OK'
end program
