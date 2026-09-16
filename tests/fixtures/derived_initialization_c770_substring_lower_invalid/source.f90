module component_definition
implicit none
integer, target, save :: target = 7
real, target, save :: other = 0.0
integer, target, save :: values(4) = [2,3,5,7]
character(3), target, save :: text = 'abc'
integer :: index = 1
type :: record
character(:), pointer :: alias => text(index:2)
end type
end module
