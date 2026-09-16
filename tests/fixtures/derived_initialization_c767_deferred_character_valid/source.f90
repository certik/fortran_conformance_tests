module component_definition
implicit none
character(3), target, save :: target = 'abc'
type :: record
character(:), pointer :: empty => null()
character(:), pointer :: alias => target
end type
end module
