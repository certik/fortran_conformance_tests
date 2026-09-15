module private_parent
implicit none
abstract interface
    subroutine action_interface(tag)
        integer, intent(out) :: tag
    end subroutine
end interface
type, abstract :: parent
contains
procedure(action_interface), deferred, nopass, private :: action
end type
end module
