module definitions
implicit none
type :: leaf
    sequence
    integer :: payload
end type
type :: record
    sequence
    type(leaf) :: member
end type
end module
