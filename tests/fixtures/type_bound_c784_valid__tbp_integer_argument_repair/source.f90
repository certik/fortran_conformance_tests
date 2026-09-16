module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: impl
end type record
contains
subroutine impl(number)
integer, intent(in) :: number
end subroutine impl
end module tbp_defs
