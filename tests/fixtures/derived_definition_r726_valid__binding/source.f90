module definitions
implicit none
type :: record
    integer :: payload
contains
    procedure, nopass :: answer
end type
contains
integer function answer()
    answer = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
value%payload = 11
if (value%payload /= 11 .or. value%answer() /= 17) error stop 1
end program
