module child_module
use private_parent, only: parent
implicit none
type, abstract, extends(parent) :: child
end type
end module
