module definitions
implicit none
type :: record
    integer, allocatable, codimension[*] :: field[:]
end type
end module
