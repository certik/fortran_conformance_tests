module definitions
implicit none
abstract interface
    integer function iface()
    end function
end interface
type :: record
    procedure(iface), pointer, nopass :: action => null()
end type
contains
integer function implementation()
implementation = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
if (associated(value%action)) error stop 1
value%action => implementation
if (.not. associated(value%action)) error stop 2
if (value%action() /= 17) error stop 3
end program
