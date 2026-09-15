module definitions
implicit none
type :: parent(k)
    integer, kind :: k = 1
    integer :: payload
end type
type, extends(parent) :: child
end type
end module
