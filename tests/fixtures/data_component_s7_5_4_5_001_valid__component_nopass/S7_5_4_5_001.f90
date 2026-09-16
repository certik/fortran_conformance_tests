module definitions
implicit none
abstract interface
integer function iface(tag)
integer, intent(in) :: tag
end function
end interface
type :: record
integer :: payload
procedure(iface), pointer, nopass :: action
end type
contains
integer function implementation(tag)
integer, intent(in) :: tag
if (tag /= 17) error stop 5
implementation = 19
end function
end module
program p
use definitions
implicit none
type(record) :: value
value%payload = 11
nullify(value%action)
value%action => implementation
if (.not. associated(value%action)) error stop 1
if (value%action(17) /= 19) error stop 2
if (value%payload /= 11) error stop 3
end program
