module definitions
implicit none
type :: record(n)
    integer, len :: n = 2
    sequence
    integer :: payload
end type
end module
