module definitions
implicit none
type :: record
    integer, pointer, allocatable :: field
end type
end module
