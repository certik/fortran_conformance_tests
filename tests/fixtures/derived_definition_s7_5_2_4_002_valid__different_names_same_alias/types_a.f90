module types_a
use iso_c_binding, only: c_int
implicit none
type :: left_record
sequence
integer :: payload
end type
end module
