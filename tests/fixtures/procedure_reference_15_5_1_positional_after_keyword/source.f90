program procedure_reference_c1531_invalid
  implicit none
  integer :: out
  out = -1
  call mix(a=5, 2, out=out)
contains
  subroutine mix(a, b, out)
    integer, intent(in) :: a, b
    integer, intent(out) :: out
    out = 100 * a + b
  end subroutine
end program procedure_reference_c1531_invalid
