module types_b
use iso_c_binding, only: c_int
implicit none
type :: RECORD
sequence
integer :: code
character(2) :: label
end type
end module
