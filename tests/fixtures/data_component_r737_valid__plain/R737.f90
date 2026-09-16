program p
implicit none
type :: record
    integer first, second
end type
type(record) :: value
value%first = 11
value%second = 13
if (value%first /= 11 .or. value%second /= 13) error stop 1
end program
