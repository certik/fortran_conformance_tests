module definitions
implicit none
type :: root
    integer, allocatable :: seed[:]
end type
type, extends(root) :: middle
    integer :: payload
end type
type, extends(middle) :: child
    integer, allocatable :: added[:]
end type
end module
