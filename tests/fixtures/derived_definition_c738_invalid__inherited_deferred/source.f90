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
end type
end module
