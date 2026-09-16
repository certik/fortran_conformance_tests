program p
implicit none
type :: record(n)
    integer, len :: n
    character(len=n) :: field
end type
type(record(2)) :: first
type(record(3)) :: second
first%field = 'AB'
second%field = 'CDE'
if (len(first%field) /= 2 .or. len(second%field) /= 3) error stop 1
if (first%field /= 'AB' .or. second%field /= 'CDE') error stop 2
end program
