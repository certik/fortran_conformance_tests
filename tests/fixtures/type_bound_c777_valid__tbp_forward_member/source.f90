module tbp_defs
implicit none
type :: record
contains
generic :: g => specific
procedure, nopass :: specific => impl
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
