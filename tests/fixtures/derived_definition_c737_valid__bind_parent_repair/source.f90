module definitions
use iso_c_binding, only: c_int
implicit none
type :: good_parent
end type
type, bind(c) :: c_parent
integer(c_int) :: seed
end type
type, extends(good_parent) :: child
integer :: payload
end type
end module
