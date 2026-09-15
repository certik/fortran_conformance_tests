module types_a
use iso_c_binding, only: c_int
implicit none
type :: record
sequence
integer(c_int) :: payload
end type
end module
