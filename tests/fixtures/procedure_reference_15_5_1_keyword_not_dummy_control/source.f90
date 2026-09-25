program procedure_reference_c1532_control
  implicit none
  integer :: x, missing, out
  x = 5; missing = -99; out = -1
  call one(a=x)
  if (out /= 6) error stop 1
  if (missing /= -99) error stop 2
  print '(a)', 'PROCEDURE REFERENCE C1532 CONTROL OK'
contains
  subroutine one(a)
    integer, intent(in) :: a
    out = a + 1
  end subroutine
end program procedure_reference_c1532_control
