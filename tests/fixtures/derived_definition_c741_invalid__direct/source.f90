module definitions
implicit none
type :: empty_parent
end type
type :: co_parent
integer, allocatable :: seed[:]
end type
type, extends(empty_parent) :: child
integer, allocatable :: added[:]
end type
end module
