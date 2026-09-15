module types_a
use iso_c_binding, only: c_int
implicit none
type, bind(c) :: record
integer(c_int) :: first, second
end type
end module
