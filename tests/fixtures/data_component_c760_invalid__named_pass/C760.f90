module definitions
implicit none
type :: record
integer :: payload
procedure(iface), pointer, pass(self), pass(self) :: action
end type
abstract interface
subroutine iface(self)
import :: record
class(record), intent(in) :: self
end subroutine
end interface
end module
