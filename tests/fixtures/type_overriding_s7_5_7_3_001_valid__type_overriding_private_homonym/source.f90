module overriding_provider
implicit none
private
public :: dispatch
type, public :: parent
integer :: parent_token
contains
procedure, private :: work => parent_work
end type parent
contains
integer function parent_work(self) result(value)
class(parent), intent(in) :: self
if (self%parent_token /= 17) error stop 101
value=7
end function parent_work
integer function dispatch(self) result(value)
class(parent), intent(in) :: self
value=self%work()
end function dispatch
end module overriding_provider
module unrelated_extension
use overriding_provider, only: parent
implicit none
private
type, public, extends(parent) :: child
contains
procedure, public, nopass :: work => foreign_work
end type child
contains
integer function foreign_work() result(value)
value=9
end function foreign_work
end module unrelated_extension
program p
use overriding_provider, only: parent, dispatch
use unrelated_extension, only: child
implicit none
type(parent) :: base
type(child) :: extended
base%parent_token=17
extended%parent%parent_token=17
call expect_value('private-parent-helper',dispatch(base),7)
call expect_value('private-child-helper',dispatch(extended),7)
call expect_value('public-homonym',extended%work(),9)
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
