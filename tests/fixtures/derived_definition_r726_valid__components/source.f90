module definitions
implicit none
abstract interface
    integer function answer_interface()
    end function
end interface
type :: record
    integer :: payload
    procedure(answer_interface), pointer, nopass :: answer
end type
contains
integer function answer_implementation()
    answer_implementation = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
value%payload = 11
value%answer => answer_implementation
if (.not. associated(value%answer)) error stop 1
if (value%payload /= 11) error stop 2
if (value%answer() /= 17) error stop 3
end program
