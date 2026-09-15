module types_b
use iso_c_binding, only: c_int
implicit none
type :: right_record
sequence
integer :: payload
end type
end module
