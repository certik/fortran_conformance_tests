module definitions
use iso_fortran_env, only: lock_type
implicit none
type, extends(lock_type) :: child
    integer :: payload
end type
end module
