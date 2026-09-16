module tbp_defs
implicit none
type :: first
integer :: payload
contains
procedure :: first_value
procedure :: explicit_first => first_value
end type first
type :: second
integer :: payload
contains
procedure :: second_value
procedure :: explicit_second => second_value
end type second
contains
subroutine prepare_first(item)
type(first), intent(inout) :: item
item%payload = 17
end subroutine prepare_first
subroutine prepare_second(item)
type(second), intent(inout) :: item
item%payload = 29
end subroutine prepare_second
integer function first_value(self) result(value)
class(first), intent(in) :: self
value = self%payload
end function first_value
integer function second_value(self) result(value)
class(second), intent(in) :: self
value = 2*self%payload+1
end function second_value
end module tbp_defs
program p
use tbp_defs
implicit none
type(first) :: a
type(second) :: b
integer :: observed
call prepare_first(a)
call prepare_second(b)
observed = a%first_value()
if (observed /= 17) error stop 1
observed = a%explicit_first()
if (observed /= 17) error stop 2
observed = b%second_value()
if (observed /= 59) error stop 3
observed = b%explicit_second()
if (observed /= 59) error stop 4
end program p
