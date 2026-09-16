module generic_types
implicit none
type :: parent
    integer :: payload
contains
    procedure :: pi => parent_integer
    generic :: g => pi
end type
type, extends(parent) :: child
    integer :: marker
contains
    procedure :: cr => child_real
    generic :: g => cr
end type
type, extends(parent) :: overriding_child
    integer :: marker
contains
    procedure :: pi => override_integer
    procedure :: cr => override_real
    generic :: g => cr
end type
type, extends(parent) :: separate_child
    integer :: marker
contains
    procedure :: cr => separate_real
    generic :: h => cr
end type
contains
integer function parent_integer(self,x) result(value)
class(parent), intent(in) :: self
integer, intent(in) :: x
if (self%payload /= 17 .or. x /= 1) error stop 21
value = 11
end function
integer function override_integer(self,x) result(value)
class(overriding_child), intent(in) :: self
integer, intent(in) :: x
if (self%payload /= 17 .or. self%marker /= 41 .or. x /= 1) error stop 22
value = 33
end function
integer function child_real(self,x) result(value)
class(child), intent(in) :: self
real, intent(in) :: x
if (self%payload /= 17 .or. self%marker /= 31 .or. x /= 1.0) error stop 23
value = 22
end function
integer function override_real(self,x) result(value)
class(overriding_child), intent(in) :: self
real, intent(in) :: x
if (self%payload /= 17 .or. self%marker /= 41 .or. x /= 1.0) error stop 23
value = 22
end function
integer function separate_real(self,x) result(value)
class(separate_child), intent(in) :: self
real, intent(in) :: x
if (self%payload /= 17 .or. self%marker /= 43 .or. x /= 1.0) error stop 23
value = 22
end function
end module
