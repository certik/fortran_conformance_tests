module definitions
implicit none
type :: good_parent
end type
integer, parameter :: selector = 1
type, extends(good_parent) :: child
integer :: payload
end type
end module
