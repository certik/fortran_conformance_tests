module definitions
use iso_fortran_env, only: lock_type
implicit none
type :: parent
    integer, allocatable :: co[:]
    type(lock_type) :: seed
end type
type, extends(parent) :: child
    type(lock_type) :: added
end type
end module
