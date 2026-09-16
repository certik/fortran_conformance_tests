module definitions
implicit none
abstract interface
subroutine callback()
end subroutine
end interface
type :: record
integer :: payload
procedure(iface), pointer :: action
end type
abstract interface
subroutine iface(self)
import :: record, callback
procedure(callback) :: self
end subroutine
end interface
end module
