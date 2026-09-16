module definitions
implicit none
type :: leaf
integer, allocatable :: co[:]
end type
type :: record
    type(leaf), pointer :: field
end type
end module
