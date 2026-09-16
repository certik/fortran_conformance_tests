module component_definition
implicit none
type :: record(width)
integer, len :: width = 2
integer :: value(width:3)
end type
end module
