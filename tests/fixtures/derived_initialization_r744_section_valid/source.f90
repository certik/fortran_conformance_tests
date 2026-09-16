module component_definition
implicit none
integer, target, save :: scalar = 7
integer, target, save :: values(4) = [2,3,5,7]
character(4), target, save :: text = 'abcd'
type :: record
integer, pointer :: alias(:) => values(1:4:2)
end type
end module
