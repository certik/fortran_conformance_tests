module parameter_definition
implicit none
type :: packet(tag,width)
integer, kind :: tag = 2
integer, len :: width = 3
end type
end module
