module component_definition
implicit none
integer, target, save :: target = 7
type :: record
integer, pointer :: alias => target
end type
end module
