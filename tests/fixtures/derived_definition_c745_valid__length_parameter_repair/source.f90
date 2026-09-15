module definitions
implicit none
type :: record(n)
    integer, len :: n = 2
    integer :: payload
end type
end module
