module types_a
use iso_c_binding, only: c_int
implicit none
type :: record
sequence
integer, pointer :: payload(:)
end type
end module
