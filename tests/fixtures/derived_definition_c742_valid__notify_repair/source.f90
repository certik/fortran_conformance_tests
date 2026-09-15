module definitions
use iso_fortran_env, only: notify_type
implicit none
type :: parent
    integer, allocatable :: co[:]
    type(notify_type) :: seed
end type
type, extends(parent) :: child
    type(notify_type) :: added
end type
end module
