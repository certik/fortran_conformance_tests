module tbp_defs
implicit none
type :: record
integer :: payload
contains
procedure :: alias => implementation
end type record
contains
subroutine prepare(item)
type(record), intent(inout) :: item
item%payload = 17
end subroutine prepare
integer function implementation(self,scale) result(value)
class(record), intent(in) :: self
integer, intent(in) :: scale
value = self%payload+scale
end function implementation
end module tbp_defs
program p
use tbp_defs
implicit none
type(record) :: item
integer :: observed
call prepare(item)
observed = item%alias(scale=3)
if (observed /= 20) error stop 1
end program p
