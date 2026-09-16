module definitions
use iso_c_binding, only: c_funptr
implicit none
type :: record
    integer, allocatable :: field[:]
end type
end module
