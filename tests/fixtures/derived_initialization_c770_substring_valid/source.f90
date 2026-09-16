module component_definition
implicit none
integer, target, save :: target = 7
real, target, save :: other = 0.0
integer, target, save :: values(4) = [2,3,5,7]
character(3), target, save :: text = 'abc'
type :: record
character(:), pointer :: alias => text(1:2)
end type
end module
