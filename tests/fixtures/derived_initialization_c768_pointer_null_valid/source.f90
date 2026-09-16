module component_definition
implicit none
integer, target, save :: target = 7
type :: record
integer, pointer :: alias => null()
end type
end module
