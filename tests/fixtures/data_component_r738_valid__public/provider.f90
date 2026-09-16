module provider
implicit none
type, public :: record
private
integer, public :: field
end type
type(record) :: published
contains
subroutine initialize()
published%field = 11
end subroutine
integer function inspect()
inspect = published%field
end function
end module
