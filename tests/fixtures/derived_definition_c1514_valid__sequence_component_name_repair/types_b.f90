module types_b
use iso_c_binding, only: c_int
implicit none
type :: record
sequence
integer :: renamed_payload
end type
end module
