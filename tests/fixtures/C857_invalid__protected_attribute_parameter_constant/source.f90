module protected_attribute_parameter_control_m
  implicit none
  integer, parameter, protected :: c = 5
end module
program main
  use protected_attribute_parameter_control_m, only: c
  implicit none
  if (c /= 5) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE PARAMETER CONTROL OK'
end program
