module definitions
implicit none
type :: record
    integer, pointer, contiguous :: field
end type
end module
