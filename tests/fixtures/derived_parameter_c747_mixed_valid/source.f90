module parameter_definition
implicit none
type :: packet(tag,width)
integer, kind :: tag
integer, len :: width
end type
end module
