module definitions
implicit none
type :: record
integer :: payload
procedure(iface), pointer :: action
end type
abstract interface
subroutine iface(self)
import :: record
class(record), pointer, intent(in) :: self
end subroutine
end interface
end module
