module types_b
use iso_c_binding, only: c_int
implicit none
type :: record
sequence
integer :: y,x
end type
end module
