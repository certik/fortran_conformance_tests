module component_definition
implicit none
integer, target, save :: target = 7
real, target, save :: other = 0.0
integer, target, save :: values(4) = [2,3,5,7]
character(3), target, save :: text = 'abc'
type :: record
integer, pointer :: scalar => target
integer, pointer :: vector(:) => values
character(3), pointer :: word => text
end type
end module
