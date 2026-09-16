module component_definition
implicit none
type :: parent
integer :: value
end type
type, extends(parent) :: child
integer :: extra
end type
type(child), target, save :: target
type :: record
class(parent), pointer :: alias => target
end type
end module
