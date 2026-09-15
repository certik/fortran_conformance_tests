module definitions
use iso_fortran_env, only: notify_type, event_type
implicit none
type :: parent
    integer, allocatable :: co[:]
    type(notify_type) :: seed
end type
type, extends(parent) :: child
    type(event_type) :: added
end type
end module
