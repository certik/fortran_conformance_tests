module definitions
implicit none
type :: record
    integer, allocatable, dimension(2,3) :: field
end type
end module
