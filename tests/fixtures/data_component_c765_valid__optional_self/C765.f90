module definitions
implicit none
type :: record
integer :: payload
procedure(iface), pointer :: action
end type
abstract interface
subroutine iface(self,tag)
import :: record
class(record), optional, intent(in) :: self
integer, intent(inout) :: tag
end subroutine
end interface
contains
subroutine implementation(self,tag)
class(record), optional, intent(in) :: self
integer, intent(inout) :: tag
if (.not. present(self)) error stop 5
if (self%payload /= 11 .or. tag /= 17) error stop 6
tag = 19
end subroutine
end module
program p
use definitions
implicit none
type(record) :: value
integer :: tag
value%payload = 11
tag = 17
nullify(value%action)
value%action => implementation
if (.not. associated(value%action)) error stop 1
call value%action(tag)
if (tag /= 19 .or. value%payload /= 11) error stop 2
end program
