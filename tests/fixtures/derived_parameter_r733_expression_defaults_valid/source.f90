module parameter_definition
implicit none
type :: packet(left,right)
integer, kind :: right = (2+3), left
end type
end module
