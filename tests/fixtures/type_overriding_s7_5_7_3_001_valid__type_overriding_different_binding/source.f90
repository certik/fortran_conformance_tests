module overriding_provider
implicit none
private
public :: dispatch
type, public :: parent
integer :: parent_token
contains
procedure, public :: work => parent_work
end type parent
type, public, extends(parent) :: child
integer :: child_token
contains
procedure, public :: extra => child_extra
end type child
contains
integer function parent_work(self) result(value)
class(parent), intent(in) :: self
if (self%parent_token /= 17) error stop 101
value=11
end function parent_work
integer function child_extra(self) result(value)
class(child), intent(in) :: self
if (self%parent_token /= 17) error stop 101
if (self%child_token /= 29) error stop 102
value=33
end function child_extra
integer function dispatch(self) result(value)
class(parent), intent(in) :: self
value=self%work()
end function dispatch
end module overriding_provider
program p
use overriding_provider, only: parent, child, dispatch
implicit none
type(parent) :: base
type(child) :: extended
base%parent_token=17
extended%child_token=29
extended%parent%parent_token=17
call expect_value('parent-direct',base%work(),11)
call expect_value('inherited-direct',extended%work(),11)
call expect_value('inherited-helper',dispatch(extended),11)
call expect_value('extra-direct',extended%extra(),33)
contains
subroutine expect_value(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual /= expected) then
print *, 'OBSERVATION',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
end subroutine expect_value
end program p
