module definitions
implicit none
type :: record
    integer, contiguous, pointer :: field(:)
end type
end module
