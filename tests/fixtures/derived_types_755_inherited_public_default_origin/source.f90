module derived_types_755_inherited_access
implicit none
type :: parent
  integer :: payload
contains
  procedure :: inherited => parent_value
end type
type, extends(parent) :: child
contains
  private
  procedure, public :: own => child_value
end type
type(child) :: object
contains
subroutine prepare()
  object%payload = 17
end subroutine
integer function parent_value(self) result(value)
  class(parent), intent(in) :: self
  value = self%payload
end function
integer function parent_value_shifted(self) result(value)
  class(parent), intent(in) :: self
  value = self%payload + 1
end function
integer function child_value(self) result(value)
  class(child), intent(in) :: self
  value = self%payload + 1
end function
end module
program main
use derived_types_755_inherited_access, only: object, prepare
implicit none
integer :: observed
call prepare()
observed = object%inherited()
if (observed /= 17) error stop 1
observed = object%own()
if (observed /= 18) error stop 2
print '(a)', 'derived_types_755 s005 inherited access ok'
end program
