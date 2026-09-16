module definitions
implicit none
type :: record
    integer, pointer, pointer :: field(:)
end type
end module
