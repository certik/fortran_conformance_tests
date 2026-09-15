module definitions
use iso_fortran_env, only: lock_type
implicit none
type :: parent
    integer, allocatable :: co[:]
end type
type, extends(parent) :: child
    type(lock_type) :: added
end type
end module
