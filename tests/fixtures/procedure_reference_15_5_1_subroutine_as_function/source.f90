program procedure_reference_c1523_invalid
  implicit none
  interface
    subroutine sub(n)
      integer, intent(in) :: n
    end subroutine
  end interface
  integer :: x
  x = sub(4)
end program procedure_reference_c1523_invalid
