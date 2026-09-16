program p
implicit none
type :: record
    integer :: field(2:1), other
end type
type(record) :: value
value%other = 11
if (rank(value%field) /= 1 .or. size(value%field) /= 0) error stop 1
if (any(shape(value%field) /= [0])) error stop 2
if (value%other /= 11) error stop 3
end program
