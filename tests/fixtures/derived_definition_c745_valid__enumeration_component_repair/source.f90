module definitions
implicit none
enumeration type :: category
enumerator :: one
end enumeration type
type :: record
sequence
integer :: payload
end type
end module
