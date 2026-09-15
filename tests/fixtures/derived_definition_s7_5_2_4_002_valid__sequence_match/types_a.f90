module types_a
use iso_c_binding, only: c_int
implicit none
type :: record
sequence
integer :: code
character(2) :: label
end type
end module
