module definitions
use iso_c_binding, only: c_int
implicit none
type, bind(c) :: record
    integer(c_int) :: payload
end type
end module
