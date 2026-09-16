module tbp_defs
implicit none
abstract interface
subroutine iface()
end subroutine iface
end interface
type, abstract :: record
contains
procedure(iface), deferred, nopass :: pending
procedure, non_overridable, nopass :: stable => impl
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
