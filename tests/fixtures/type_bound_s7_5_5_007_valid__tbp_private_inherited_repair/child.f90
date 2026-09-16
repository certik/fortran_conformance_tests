module tbp_child
use tbp_provider, only: parent
implicit none
type, extends(parent) :: child
integer :: marker
end type child
type(child) :: child_object
end module tbp_child
