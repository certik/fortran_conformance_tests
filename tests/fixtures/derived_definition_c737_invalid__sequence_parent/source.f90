module definitions
implicit none
type :: good_parent
end type
type :: seq_parent
sequence
integer :: seed
end type
type, extends(seq_parent) :: child
integer :: payload
end type
end module
