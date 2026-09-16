module definitions
implicit none
type :: record
integer :: payload
contains
procedure :: action => implementation
end type
contains
subroutine implementation(self,tag)
class(record), target, intent(in) :: self
integer, intent(inout) :: tag
if (self%payload /= 11 .or. tag /= 17) error stop 6
tag = 19
end subroutine
end module
program p
use definitions
implicit none
type(record), target :: value
integer :: tag
value%payload = 11
tag = 17
call value%action(tag)
if (tag /= 19 .or. value%payload /= 11) error stop 2
end program
