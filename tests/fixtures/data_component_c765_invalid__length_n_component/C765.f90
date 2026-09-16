module definitions
implicit none
type :: record(n,m)
integer, len :: n,m
character(n) :: label
integer :: values(m)
procedure(iface), pointer :: action
end type
abstract interface
subroutine iface(self)
import :: record
class(record(2,*)), intent(in) :: self
end subroutine
end interface
end module
