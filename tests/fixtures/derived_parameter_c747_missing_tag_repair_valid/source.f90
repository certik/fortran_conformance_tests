module parameter_definition
implicit none
type :: packet(tag,width)
integer, len :: width
integer, kind :: tag
end type
end module
