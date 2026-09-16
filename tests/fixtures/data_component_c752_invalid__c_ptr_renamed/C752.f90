module definitions
use iso_c_binding, only: handle => c_ptr
implicit none
type :: record
    type(handle), allocatable :: field[:]
end type
end module
