module definitions
implicit none
type :: record
    type(record), allocatable :: next
end type
end module
