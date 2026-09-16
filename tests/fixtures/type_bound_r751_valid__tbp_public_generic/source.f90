module tbp_defs
implicit none
type :: record
contains
private
procedure, nopass :: specific => impl
generic, public :: g => specific
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
