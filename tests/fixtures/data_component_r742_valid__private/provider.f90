module provider
implicit none
abstract interface
integer function iface()
end function
end interface
type, public :: record
procedure(iface), pointer, nopass, private :: action
end type
type(record) :: published
contains
subroutine initialize()
published%action => implementation
end subroutine
integer function inspect()
if (.not. associated(published%action)) error stop 1
inspect = published%action()
end function
integer function implementation()
implementation = 17
end function
end module
