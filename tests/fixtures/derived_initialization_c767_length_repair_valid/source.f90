module component_definition
implicit none
type :: record(width)
integer, len :: width = 2
character(width) :: value
end type
end module
