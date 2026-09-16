module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: first => impl, second => impl
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
