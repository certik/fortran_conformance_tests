module definitions
implicit none
abstract interface
    subroutine action_interface(tag)
        integer, intent(out) :: tag
    end subroutine
end interface
type, abstract :: parent
contains
procedure(action_interface), deferred, nopass :: action
end type

type, extends(parent) :: child
    integer :: payload
contains
    procedure, nopass :: action => implementation
end type
contains
subroutine implementation(tag)
    integer, intent(out) :: tag
    tag = 17
end subroutine
end module
program p
use definitions
implicit none
type(child) :: value
integer :: tag
value%payload = 11
call value%action(tag)
if (tag /= 17 .or. value%payload /= 11) error stop 1
end program
