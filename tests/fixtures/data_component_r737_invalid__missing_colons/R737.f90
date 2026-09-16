module definitions
implicit none
type :: record
    integer, pointer field(:)
end type
end module
