module definitions
implicit none
type :: record
    integer, codimension[:], allocatable :: field
end type
end module
