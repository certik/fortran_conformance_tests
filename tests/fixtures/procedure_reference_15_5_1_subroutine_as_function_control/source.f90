program procedure_reference_c1523_control
  implicit none
  interface
    integer function sub(n)
      integer, intent(in) :: n
    end function
  end interface
  integer :: x
  x = -9
  x = sub(4)
  if (x /= 5) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1523 CONTROL OK'
end program procedure_reference_c1523_control
integer function sub(n)
  integer, intent(in) :: n
  sub = n + 1
end function sub
