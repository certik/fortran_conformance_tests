module procedure_reference_c1527_m
  implicit none
  type parent
    integer :: value = -1
  contains
    procedure :: parent_set
  end type
  type, extends(parent) :: child
  contains
    procedure :: child_only
  end type
contains
  subroutine parent_set(self)
    class(parent), intent(inout) :: self
    self%value = 11
  end subroutine
  subroutine child_only(self)
    class(child), intent(inout) :: self
    self%value = 99
  end subroutine
end module procedure_reference_c1527_m
program procedure_reference_c1527_control
  use procedure_reference_c1527_m
  implicit none
  class(parent), allocatable :: obj
  allocate(child :: obj)
  call obj%parent_set()
  if (obj%value /= 11) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1527 CONTROL OK'
end program procedure_reference_c1527_control
