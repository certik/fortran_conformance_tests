module definitions
implicit none
type :: record(k)
    integer, kind :: k = 1
    sequence
    integer :: payload
end type
end module
