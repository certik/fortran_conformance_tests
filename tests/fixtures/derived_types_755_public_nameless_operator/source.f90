module derived_types_755_public_operator
implicit none
private
type, public :: record
  private
  integer :: payload
contains
  procedure, private :: op_impl
  generic, public :: operator(.get.) => op_impl
end type
type(record), public :: object
public :: prepare
contains
subroutine prepare()
  object%payload = 17
end subroutine
integer function op_impl(self) result(value)
  class(record), intent(in) :: self
  value = self%payload
end function
integer function op_impl_shifted(self) result(value)
  class(record), intent(in) :: self
  value = self%payload + 1
end function
end module
program main
use derived_types_755_public_operator, only: object, prepare
implicit none
integer :: observed
call prepare()
observed = .get. object
if (observed /= 17) error stop 1
print '(a)', 'derived_types_755 s006 public nameless ok'
end program
