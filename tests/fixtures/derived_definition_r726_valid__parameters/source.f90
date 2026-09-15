module definitions
implicit none
type :: record(k,n)
    integer, kind :: k = 1
    integer, len :: n = 2
    private
    integer :: payload(n)
end type
contains
subroutine check()
    type(record(1,2)) :: value
    value%payload = [11,13]
    if (value%k /= 1 .or. value%n /= 2) error stop 1
    if (size(value%payload) /= 2) error stop 2
    if (any(value%payload /= [11,13])) error stop 3
end subroutine
end module
program p
use definitions, only: check
implicit none
call check()
end program
