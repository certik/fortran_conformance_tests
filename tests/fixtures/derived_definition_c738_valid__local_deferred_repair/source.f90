module definitions
implicit none
abstract interface
    subroutine action_interface(tag)
        integer, intent(out) :: tag
    end subroutine
end interface
type, abstract :: record
contains
procedure(action_interface), deferred, nopass :: action
end type
end module
