module overriding_provider
implicit none
private
public :: dispatch
type, public :: root
integer :: root_token
contains
procedure, public :: work => root_work
end type root
type, public, extends(root) :: child
integer :: child_token
contains
procedure, public :: work => child_work
end type child
type, public, extends(child) :: grand
end type grand
contains
integer function root_work(self) result(value)
class(root), intent(in) :: self
if (self%root_token /= 17) error stop 101
value=11
end function root_work
integer function child_work(self) result(value)
class(child), intent(in) :: self
if (self%root_token /= 17) error stop 101
if (self%child_token /= 29) error stop 102
value=22
end function child_work
integer function dispatch(self) result(value)
class(root), intent(in) :: self
value=self%work()
end function dispatch
end module overriding_provider
program p
use overriding_provider, only: root, grand, dispatch
implicit none
type(root) :: original
type(grand) :: last
original%root_token=17
last%child%child_token=29
last%child%root%root_token=17
call expect_value('root-direct',original%work(),11)
call expect_value('root-helper',dispatch(original),11)
call expect_value('grand-helper',dispatch(last),22)
call expect_value('grand-direct',last%work(),22)
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
