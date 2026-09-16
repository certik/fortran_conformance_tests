module tbp_defs
implicit none
type :: record
contains
procedure, non_overridable, nopass :: act => impl
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
