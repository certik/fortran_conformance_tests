module definitions
use iso_fortran_env, only: event_type
implicit none
type, extends(event_type) :: child
    integer :: payload
end type
end module
