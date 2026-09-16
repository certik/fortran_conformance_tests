module definitions
implicit none
type :: leaf
integer :: payload
end type
type :: record
    type(leaf) :: field
end type
end module
