module definitions
implicit none
type :: record
    integer, allocatable, allocatable :: field(:)
end type
end module
