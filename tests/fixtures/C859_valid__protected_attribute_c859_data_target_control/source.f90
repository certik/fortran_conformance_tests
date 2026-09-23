module protected_attribute_c859_target_m
  implicit none
  integer, target :: x = 11
end module
program main
  use protected_attribute_c859_target_m, only: x
  implicit none
  integer, pointer :: q
  q => x
  if (q /= 11) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 DATA TARGET CONTROL OK'
end program
