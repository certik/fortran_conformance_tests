module component_definition
implicit none
type :: record(width)
integer, len :: width = 2
integer :: value(width:3) = 2
end type
end module
