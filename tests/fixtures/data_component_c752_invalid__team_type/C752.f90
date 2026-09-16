module definitions
use iso_fortran_env, only: team_type
implicit none
type :: record
    type(team_type), allocatable :: field[:]
end type
end module
