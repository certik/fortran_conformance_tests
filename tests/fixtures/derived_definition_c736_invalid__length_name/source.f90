module definitions
implicit none
type :: record(n,N)
    integer, len :: n = 2
    integer :: payload
end type
end module
