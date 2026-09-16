module component_definition
implicit none
integer, allocatable, target, save :: target
type :: record
integer, pointer :: alias => target
end type
end module
