program p
implicit none
type :: record
    character(len=3) :: first, second
    integer :: left, right
end type
type(record) :: value
value%first = 'ABC'
value%second = 'DEF'
value%left = 11
value%right = 13
if (len(value%first) /= 3 .or. len(value%second) /= 3) error stop 1
if (value%first /= 'ABC' .or. value%second /= 'DEF') error stop 2
if (value%left /= 11 .or. value%right /= 13) error stop 3
end program
