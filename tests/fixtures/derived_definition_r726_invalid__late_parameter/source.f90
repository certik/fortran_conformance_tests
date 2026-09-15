module definitions
implicit none
type :: record(k)
    integer :: payload
    integer, kind :: k = 1
end type
end module
