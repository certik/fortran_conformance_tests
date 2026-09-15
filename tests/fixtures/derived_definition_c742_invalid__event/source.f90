module definitions
use iso_fortran_env, only: event_type
implicit none
type :: parent
    integer, allocatable :: co[:]
end type
type, extends(parent) :: child
    type(event_type) :: added
end type
end module
