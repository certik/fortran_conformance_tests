module definitions
implicit none
type :: record
    integer, allocatable, dimension(:,:) :: field
end type
end module
