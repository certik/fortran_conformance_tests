module tbp_defs
implicit none
abstract interface
subroutine iface()
end subroutine iface
end interface
type, abstract :: record
contains
procedure(iface), deferred, deferred, nopass :: act
end type record
end module tbp_defs
