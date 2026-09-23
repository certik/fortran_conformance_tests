module derived_types_755_dynamic_specific
implicit none
type :: parent
  integer :: payload
contains
  procedure :: value => parent_value
  generic :: choose => value
end type
type, extends(parent) :: child
contains
  procedure :: value => child_value
  procedure :: real_value => child_real_value
  generic :: choose => real_value
end type
contains
integer function parent_value(self, n) result(value)
  class(parent), intent(in) :: self
  integer, intent(in) :: n
  value = self%payload + n
end function
integer function child_value(self, n) result(value)
  class(child), intent(in) :: self
  integer, intent(in) :: n
  value = 10*self%payload + n
end function
integer function child_value_shifted(self, n) result(value)
  class(child), intent(in) :: self
  integer, intent(in) :: n
  value = 10*self%payload + n + 1
end function
integer function child_real_value(self, x) result(value)
  class(child), intent(in) :: self
  real, intent(in) :: x
  value = 100*self%payload + int(x)
end function
end module
program main
use derived_types_755_dynamic_specific
implicit none
type(child), target :: actual
class(parent), pointer :: view
integer :: observed
actual%payload = 4
view => actual
observed = view%choose(2)
if (observed /= 42) error stop 1
observed = actual%choose(3.0)
if (observed /= 403) error stop 2
print '(a)', 'derived_types_755 s003 dynamic specific ok'
end program
