module overriding_provider
implicit none
private
public :: dispatch
type, public :: root
integer :: root_token
contains
procedure, public :: work => root_work
end type root
type, public, extends(root) :: middle
end type middle
type, public, extends(middle) :: leaf
integer :: leaf_token
contains
procedure, public :: work => leaf_work
end type leaf
contains
integer function root_work(self) result(value)
class(root), intent(in) :: self
if (self%root_token /= 17) error stop 101
value=11
end function root_work
integer function leaf_work(self) result(value)
class(leaf), intent(in) :: self
if (self%root_token /= 17) error stop 101
if (self%leaf_token /= 41) error stop 102
value=33
end function leaf_work
integer function dispatch(self) result(value)
class(root), intent(in) :: self
value=self%work()
end function dispatch
end module overriding_provider
program p
use overriding_provider, only: root, leaf, dispatch
implicit none
type(root) :: original
type(leaf) :: last
original%root_token=17
last%leaf_token=41
last%middle%root%root_token=17
call expect_value('root-direct',original%work(),11)
call expect_value('root-helper',dispatch(original),11)
call expect_value('leaf-helper',dispatch(last),33)
call expect_value('explicit-middle',last%middle%work(),11)
call expect_value('leaf-direct',last%work(),33)
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
