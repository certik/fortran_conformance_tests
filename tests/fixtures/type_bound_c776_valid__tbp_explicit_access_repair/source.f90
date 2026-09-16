module tbp_defs
implicit none
type :: record
contains
procedure :: int_case => integer_impl
procedure :: real_case => real_impl
generic, public :: g => int_case
generic, public :: g => real_case
end type record
contains
integer function integer_impl(self,n) result(value)
class(record), intent(in) :: self
integer, intent(in) :: n
value = 11
end function integer_impl
integer function real_impl(self,x) result(value)
class(record), intent(in) :: self
real, intent(in) :: x
value = 22
end function real_impl
end module tbp_defs
