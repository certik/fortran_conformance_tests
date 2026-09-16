module definitions
use iso_c_binding, only: handle => c_funptr
implicit none
type :: record
    type(handle), allocatable :: field[:]
end type
end module
