module parameter_definition
implicit none
type :: packet(tag,extra)
integer, kind :: tag
integer, len :: extra
end type
end module
