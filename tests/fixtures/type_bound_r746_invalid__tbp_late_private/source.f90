module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: act => impl
private
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
