module child_module
use private_parent, only: parent
implicit none
type, extends(parent) :: child
end type
end module
