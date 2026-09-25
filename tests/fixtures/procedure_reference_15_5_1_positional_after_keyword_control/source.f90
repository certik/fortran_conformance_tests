program procedure_reference_c1531_control
  implicit none
  integer :: out
  out = -1
  call mix(a=5, b=2, out=out)
  if (out /= 502) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1531 CONTROL OK'
contains
  subroutine mix(a, b, out)
    integer, intent(in) :: a, b
    integer, intent(out) :: out
    out = 100 * a + b
  end subroutine
end program procedure_reference_c1531_control
