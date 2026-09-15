module definitions
use iso_c_binding, only: c_funptr
implicit none
type :: good_parent
end type
type, extends(good_parent) :: child
integer :: payload
end type
end module
