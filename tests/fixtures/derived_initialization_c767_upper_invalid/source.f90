module component_definition
implicit none
type :: record(width)
integer, len :: width = 2
integer :: value(1:width) = 2
end type
end module
