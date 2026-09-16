module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: specific => impl
generic :: h => specific
generic :: g => specific
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
