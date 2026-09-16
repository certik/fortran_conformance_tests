module definitions
implicit none
type :: first_type
    integer :: payload
contains
    procedure, pass(a) :: action => implementation
end type
type :: second_type
    integer :: payload
contains
    procedure, pass(b) :: action => implementation
end type
contains
integer function implementation(a,b)
class(first_type), intent(in) :: a
class(second_type), intent(in) :: b
if (a%payload /= 11 .or. b%payload /= 17) error stop 5
implementation = 19
end function
end module
program p
use definitions
implicit none
type(first_type) :: first
type(second_type) :: second
first%payload = 11
second%payload = 17
if (first%action(second) /= 19) error stop 1
if (second%action(first) /= 19) error stop 2
end program
