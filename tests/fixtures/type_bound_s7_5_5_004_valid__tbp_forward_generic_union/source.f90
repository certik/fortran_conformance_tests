module tbp_defs
implicit none
type :: record
integer :: payload
contains
generic :: g => int_case
generic :: g => real_case
procedure :: int_case => int_impl
procedure :: real_case => real_impl
end type record
contains
subroutine prepare(item,payload)
type(record), intent(inout) :: item
integer, intent(in) :: payload
item%payload = payload
end subroutine prepare
integer function int_impl(self,n) result(value)
class(record), intent(in) :: self
integer, intent(in) :: n
value = self%payload+2*n
end function int_impl
integer function real_impl(self,x) result(value)
class(record), intent(in) :: self
real, intent(in) :: x
value = self%payload+17
end function real_impl
end module tbp_defs
program p
use tbp_defs
implicit none
type(record) :: item
integer :: observed
call prepare(item,payload=5)
observed = item%g(3)
if (observed /= 11) error stop 1
observed = item%g(1.0)
if (observed /= 22) error stop 2
call prepare(item,payload=7)
observed = item%g(3)
if (observed /= 13) error stop 3
observed = item%g(1.0)
if (observed /= 24) error stop 4
end program p
