module provider
implicit none
type, private :: record
    integer :: payload
end type
contains
integer function check()
    type(record) :: value
    value%payload = 11
    check = value%payload
end function
end module
program p
use provider, only: check
implicit none
if (check() /= 11) error stop 1
end program
