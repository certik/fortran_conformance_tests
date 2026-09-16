module definitions
implicit none
type :: leaf
integer :: payload
end type
type :: record
    type(leaf) :: field*2
end type
end module
