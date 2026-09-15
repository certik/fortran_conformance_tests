module definitions
implicit none
type, public :: record
    private
    integer, public :: payload
contains
    private
    procedure, public, nopass :: answer
end type
contains
integer function answer()
    answer = 17
end function
end module
program p
use definitions, only: record
implicit none
type(record) :: value
value%payload = 11
if (value%payload /= 11 .or. value%answer() /= 17) error stop 1
end program
