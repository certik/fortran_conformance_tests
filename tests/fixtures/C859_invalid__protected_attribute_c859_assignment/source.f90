module protected_attribute_c859_assignment_m
  implicit none
  integer, protected :: x = 11
end module
program main
  use protected_attribute_c859_assignment_m, only: x
  implicit none
  x = 12
  if (x /= 12) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 ASSIGNMENT CONTROL OK'
end program
