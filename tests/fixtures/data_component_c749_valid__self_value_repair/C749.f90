module definitions
implicit none
type :: record
    type(record), pointer :: next
end type
end module
