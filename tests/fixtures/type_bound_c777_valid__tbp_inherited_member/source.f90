module tbp_defs
implicit none
type :: record
contains
procedure :: int_case => integer_impl
generic :: g => int_case
end type record
type, extends(record) :: child
contains
procedure :: real_case => child_real
generic :: h => int_case
end type child
contains
integer function integer_impl(self,n) result(value)
class(record), intent(in) :: self
integer, intent(in) :: n
value = 11
end function integer_impl
integer function child_real(self,x) result(value)
class(child), intent(in) :: self
real, intent(in) :: x
value = 22
end function child_real
end module tbp_defs
