module definitions
implicit none
type :: leaf
    integer :: payload
end type
type :: record
    sequence
    type(leaf) :: member
end type
end module
