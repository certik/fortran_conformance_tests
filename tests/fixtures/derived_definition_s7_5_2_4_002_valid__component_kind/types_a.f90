module types_a
use iso_c_binding, only: c_int
implicit none
type :: record
sequence
real(kind=kind(0.0)) :: payload
end type
end module
