module protected_attribute_c859_do_m
  implicit none
  integer, protected :: x = 11
end module
program main
  use protected_attribute_c859_do_m, only: x
  implicit none
  integer :: visits
  visits = -3
  visits = 0
  do x = 1, 2
    visits = visits + 1
  end do
  if (visits /= 2) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 DO VARIABLE CONTROL OK'
end program
