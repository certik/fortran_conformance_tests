program p
implicit none
type :: record
    integer, dimension(2,3) :: first, second
end type
type(record) :: value
value%first = 11
value%second = 13
if (rank(value%first) /= 2 .or. rank(value%second) /= 2) error stop 1
if (any(shape(value%first) /= [2,3])) error stop 2
if (any(shape(value%second) /= [2,3])) error stop 3
if (any(lbound(value%first) /= [1,1])) error stop 4
if (any(lbound(value%second) /= [1,1])) error stop 5
if (any(value%first /= 11) .or. any(value%second /= 13)) error stop 6
end program
