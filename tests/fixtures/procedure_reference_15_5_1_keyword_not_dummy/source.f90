program procedure_reference_c1532_invalid
  implicit none
  integer :: x, missing, out
  x = 5; missing = -99; out = -1
  call one(missing=x)
contains
  subroutine one(a)
    integer, intent(in) :: a
    out = a + 1
  end subroutine
end program procedure_reference_c1532_invalid
