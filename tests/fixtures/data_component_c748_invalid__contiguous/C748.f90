module definitions
implicit none
type :: record
    integer, contiguous, contiguous, pointer :: field(:)
end type
end module
