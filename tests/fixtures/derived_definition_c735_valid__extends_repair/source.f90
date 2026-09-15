module definitions
implicit none
type :: parent
end type
type, extends(parent) :: record
    integer :: payload
end type
end module
