module parameter_definition
implicit none
type :: packet(tag)
integer, kind :: tag
integer, len :: extra
end type
end module
