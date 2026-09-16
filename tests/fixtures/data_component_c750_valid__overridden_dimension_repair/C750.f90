module definitions
implicit none
type :: record
    integer, pointer, dimension(:) :: field(:)
end type
end module
