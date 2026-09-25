program procedure_reference_c1530_invalid
  implicit none
  integer :: x
  external ext
  x = 5
  call ext(a=x)
end program procedure_reference_c1530_invalid
subroutine ext(a)
  integer, intent(inout) :: a
  a = a + 1
end subroutine ext
