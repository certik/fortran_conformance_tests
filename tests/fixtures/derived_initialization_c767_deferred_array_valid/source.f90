module component_definition
implicit none
integer, target, save :: target(2) = [2,3]
type :: record
integer, pointer :: empty(:) => null()
integer, pointer :: alias(:) => target
end type
end module
