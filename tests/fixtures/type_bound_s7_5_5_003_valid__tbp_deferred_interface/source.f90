module tbp_defs
implicit none
type, abstract :: base
integer :: payload
contains
procedure(method_interface), deferred :: alias
end type base
type, extends(base) :: record
integer :: marker
contains
procedure :: alias => implementation
end type record
abstract interface
integer function method_interface(self,scale) result(value)
import base
class(base), intent(in) :: self
integer, intent(in) :: scale
end function method_interface
end interface
contains
subroutine prepare(item)
type(record), intent(inout) :: item
item%payload = 17
item%marker = 29
end subroutine prepare
integer function implementation(self,scale) result(value)
class(record), intent(in) :: self
integer, intent(in) :: scale
value = self%payload+scale
end function implementation
integer function through_base(item) result(value)
class(base), intent(in) :: item
value = item%alias(scale=3)
end function through_base
end module tbp_defs
program p
use tbp_defs
implicit none
type(record) :: item
integer :: observed
call prepare(item)
observed = through_base(item)
if (observed /= 20) error stop 1
if (item%marker /= 29) error stop 2
end program p
