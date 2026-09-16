module definitions
implicit none
type :: record
    type(record) :: next
end type
end module
