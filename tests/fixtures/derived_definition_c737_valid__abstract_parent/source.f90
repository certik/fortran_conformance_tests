module definitions
implicit none
type, abstract :: parent
    integer :: inherited
end type
type, extends(parent) :: child
end type
end module
