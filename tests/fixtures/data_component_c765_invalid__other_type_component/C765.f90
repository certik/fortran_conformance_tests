module definitions
implicit none
type :: other
integer :: payload
end type
type :: record
integer :: payload
procedure(iface), pointer :: action
end type
abstract interface
subroutine iface(self)
import :: record, other
class(other), intent(in) :: self
end subroutine
end interface
end module
