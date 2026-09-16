module definitions
implicit none
type :: leaf
integer, allocatable :: co[:]
end type
type :: record
    type(leaf) :: field
end type
end module
