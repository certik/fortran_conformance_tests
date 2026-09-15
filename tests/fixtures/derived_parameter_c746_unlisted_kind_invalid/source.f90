module parameter_definition
implicit none
type :: packet(tag)
integer, kind :: tag
integer, kind :: extra
end type
end module
