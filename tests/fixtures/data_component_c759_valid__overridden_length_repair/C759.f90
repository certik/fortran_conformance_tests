module definitions
implicit none
integer :: width = 2
type :: record
    character(len=2) :: field*2
end type
end module
