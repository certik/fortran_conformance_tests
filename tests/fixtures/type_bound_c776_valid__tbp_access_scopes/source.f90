module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: specific => impl
generic, public :: g => specific
generic, private :: h => specific
end type record
type :: another
contains
procedure, nopass :: specific => impl
generic, private :: g => specific
end type another
contains
subroutine impl()
end subroutine impl
end module tbp_defs
