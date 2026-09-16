module definitions
implicit none
type :: record
integer :: payload
procedure(iface), pointer :: action
end type
abstract interface
subroutine iface(self)
import :: record
class(record), value, intent(in) :: self
end subroutine
end interface
end module
