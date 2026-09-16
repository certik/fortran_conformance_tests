module tbp_defs
implicit none
type :: record
integer :: payload
contains
procedure :: assign => assign_impl
generic :: assignment(=) => assign
end type record
contains
subroutine assign_impl(lhs,rhs)
class(record), intent(inout) :: lhs
integer, intent(in) :: rhs
lhs%payload = rhs
end subroutine assign_impl
end module tbp_defs
