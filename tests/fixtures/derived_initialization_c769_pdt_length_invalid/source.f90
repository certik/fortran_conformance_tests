module component_definition
implicit none
type :: element(width)
integer, len :: width
character(width) :: payload
end type
type(element(3)), target, save :: target
type :: record
type(element(2)), pointer :: alias => target
end type
end module
