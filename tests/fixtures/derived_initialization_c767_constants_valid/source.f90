module component_definition
implicit none
type :: record
character(2) :: text = 'abcd'
integer :: values(-1:1) = 3
end type
end module
