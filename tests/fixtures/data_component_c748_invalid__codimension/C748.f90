module definitions
implicit none
type :: record
    integer, codimension[:], codimension[:], allocatable :: field
end type
end module
