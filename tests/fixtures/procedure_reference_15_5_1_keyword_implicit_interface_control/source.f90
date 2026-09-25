program procedure_reference_c1530_control
  implicit none
  interface
    subroutine ext(a)
      integer, intent(inout) :: a
    end subroutine
  end interface
  integer :: x
  x = 5
  call ext(a=x)
  if (x /= 6) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1530 CONTROL OK'
end program procedure_reference_c1530_control
subroutine ext(a)
  integer, intent(inout) :: a
  a = a + 1
end subroutine ext
