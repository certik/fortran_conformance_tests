module tbp_defs
implicit none
type :: record
contains
procedure, non_overridable :: act => parent_impl
end type record
type, extends(record) :: child
contains
procedure :: act => child_impl
end type child
abstract interface
subroutine parent_iface(self)
import record
class(record), intent(in) :: self
end subroutine parent_iface
subroutine child_iface(self)
import child
class(child), intent(in) :: self
end subroutine child_iface
end interface
contains
subroutine parent_impl(self)
class(record), intent(in) :: self
end subroutine parent_impl
subroutine child_impl(self)
class(child), intent(in) :: self
end subroutine child_impl
end module tbp_defs
