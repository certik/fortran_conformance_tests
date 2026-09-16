module definitions
use iso_c_binding, only: handle => c_ptr
implicit none
type :: record
    integer, allocatable :: field[:]
end type
end module
