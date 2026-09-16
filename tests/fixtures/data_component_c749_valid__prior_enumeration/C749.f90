module definitions
implicit none
enumeration type :: category
enumerator :: zero, one
end enumeration type
type :: record
    type(category) :: field
end type
end module
