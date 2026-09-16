module definitions
implicit none
type :: leaf
integer, allocatable :: co[:]
end type
type :: record
    type(leaf), allocatable :: field
end type
end module
