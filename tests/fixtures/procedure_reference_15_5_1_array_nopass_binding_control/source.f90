module procedure_reference_c1529_m
  implicit none
  type t
    integer :: value = -1
  contains
    procedure :: touch
  end type
contains
  elemental subroutine touch(self)
    class(t), intent(inout) :: self
    self%value = self%value + 10
  end subroutine
end module procedure_reference_c1529_m
program procedure_reference_c1529_control
  use procedure_reference_c1529_m
  implicit none
  type(t) :: a(2)
  a%value = [1, 2]
  call a%touch()
  if (any(a%value /= [11, 12])) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1529 CONTROL OK'
end program procedure_reference_c1529_control
