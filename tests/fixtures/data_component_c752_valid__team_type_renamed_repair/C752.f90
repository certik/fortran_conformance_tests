module definitions
use iso_fortran_env, only: handle => team_type
implicit none
type :: record
    integer, allocatable :: field[:]
end type
end module
