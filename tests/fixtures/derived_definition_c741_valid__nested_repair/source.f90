module definitions
implicit none
type :: leaf
integer, allocatable :: co[:]
end type
type :: empty_parent
end type
type :: co_parent
type(leaf) :: seed
end type
type, extends(co_parent) :: child
type(leaf) :: added
end type
end module
