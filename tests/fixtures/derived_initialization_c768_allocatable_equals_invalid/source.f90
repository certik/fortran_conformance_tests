module component_definition
implicit none
integer, target, save :: target = 7
type :: record
integer, allocatable :: value = 3
end type
end module
