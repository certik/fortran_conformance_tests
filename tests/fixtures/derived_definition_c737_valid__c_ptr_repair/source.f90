module definitions
use iso_c_binding, only: c_ptr
implicit none
type :: good_parent
end type
type, extends(good_parent) :: child
integer :: payload
end type
end module
