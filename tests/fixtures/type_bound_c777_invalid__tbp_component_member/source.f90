module tbp_defs
implicit none
type :: record
integer :: payload
contains
procedure, nopass :: specific => impl
generic :: g => payload
end type record
contains
subroutine impl()
end subroutine impl
end module tbp_defs
