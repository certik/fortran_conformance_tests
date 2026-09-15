module definitions
implicit none
type :: record(k,k)
    integer, kind :: k = 1
    integer :: payload
end type
end module
