module tbp_defs
implicit none
type, abstract :: record
contains
procedure, deferred, nopass :: impl
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
