module definitions
implicit none
integer :: width = 2
type :: record
    integer :: field(width:3)
end type
end module
