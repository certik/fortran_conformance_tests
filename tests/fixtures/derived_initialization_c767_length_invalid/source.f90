module component_definition
implicit none
type :: record(width)
integer, len :: width = 2
character(width) :: value = 'abc'
end type
end module
