program p
implicit none
type :: record
    integer :: field(-1:0,2:4)
end type
type(record) :: value
value%field = 11
value%field(0,4) = 13
if (rank(value%field) /= 2) error stop 1
if (any(shape(value%field) /= [2,3])) error stop 2
if (any(lbound(value%field) /= [-1,2])) error stop 3
if (any(ubound(value%field) /= [0,4])) error stop 4
if (value%field(-1,2) /= 11 .or. value%field(0,4) /= 13) error stop 5
end program
