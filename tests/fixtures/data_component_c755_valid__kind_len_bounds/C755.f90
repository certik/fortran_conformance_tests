program p
implicit none
type :: record(k,n)
    integer, kind :: k
    integer, len :: n
    integer :: field(k,n)
end type
type(record(2,2)) :: first
type(record(2,3)) :: second
first%field = 11
second%field = 13
if (rank(first%field) /= 2 .or. rank(second%field) /= 2) error stop 1
if (any(shape(first%field) /= [2,2])) error stop 2
if (any(shape(second%field) /= [2,3])) error stop 3
if (any(first%field /= 11) .or. any(second%field /= 13)) error stop 4
end program
