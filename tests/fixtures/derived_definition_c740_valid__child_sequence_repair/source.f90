module definitions
implicit none
type :: parent
end type
type, extends(parent) :: child
    integer :: payload
end type
end module
