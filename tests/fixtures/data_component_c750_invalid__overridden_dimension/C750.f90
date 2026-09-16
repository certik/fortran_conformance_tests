module definitions
implicit none
type :: record
    integer, pointer, dimension(2) :: field(:)
end type
end module
