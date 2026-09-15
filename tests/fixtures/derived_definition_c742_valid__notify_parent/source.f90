module definitions
use iso_fortran_env, only: notify_type
implicit none
type, extends(notify_type) :: child
    integer :: payload
end type
end module
