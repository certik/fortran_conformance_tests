module component_definition
implicit none
integer, target, save :: target[*]
type :: record
integer, pointer :: alias => target[1]
end type
end module
