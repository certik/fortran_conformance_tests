module component_definition
implicit none
integer, target, save :: target = 7
type :: record
integer, pointer :: value = 3
end type
end module
