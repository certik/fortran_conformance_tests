subroutine local_definition
implicit none
integer, target :: target
type :: record
integer, pointer :: alias => target
end type
end subroutine
