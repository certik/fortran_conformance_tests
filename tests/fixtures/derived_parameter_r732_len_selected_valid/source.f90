module parameter_definition
implicit none
integer, parameter :: ik = selected_int_kind(18)
type :: packet(tag)
integer(ik), len :: tag
end type
end module
