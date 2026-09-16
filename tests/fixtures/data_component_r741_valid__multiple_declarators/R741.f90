module definitions
implicit none
abstract interface
integer function iface()
end function
end interface
type :: record
    procedure(iface), pointer, nopass :: first, second
end type
contains
integer function first_target()
first_target = 11
end function
integer function second_target()
second_target = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
nullify(value%first, value%second)
value%first => first_target
value%second => second_target
if (.not. associated(value%first)) error stop 1
if (.not. associated(value%second)) error stop 2
if (value%first() /= 11 .or. value%second() /= 17) error stop 3
end program
