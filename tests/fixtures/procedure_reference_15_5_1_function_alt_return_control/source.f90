program procedure_reference_c1524_control
  implicit none
  integer :: x
  x = -9
  x = f(7)
100 continue
  if (x /= 7) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1524 CONTROL OK'
contains
  integer function f(n)
    integer, intent(in) :: n
    f = n
  end function
end program procedure_reference_c1524_control
