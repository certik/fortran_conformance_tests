module definitions
implicit none
integer :: width = 2
type :: record
    integer :: field(1:width)
end type
end module
