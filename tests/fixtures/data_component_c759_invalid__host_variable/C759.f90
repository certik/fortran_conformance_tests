module definitions
implicit none
integer :: width = 2
type :: record
    character(len=width) :: field
end type
end module
