module definitions
implicit none
abstract interface
integer function iface()
end function
end interface
type :: record
    procedure(iface), pointer, nopass, public :: action
end type
end module
