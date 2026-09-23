module protected_attribute_c859_out_m
  implicit none
  integer, protected :: x = 11
end module
program main
  use protected_attribute_c859_out_m, only: x
  implicit none
  call define(x)
  if (x /= 18) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 OUT ACTUAL CONTROL OK'
contains
  subroutine define(a)
    integer, intent(out) :: a
    a = 18
  end subroutine
end program
