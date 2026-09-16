module component_definition
implicit none
type :: record(width)
integer, len :: width = 2
integer :: value(1:width)
end type
end module
