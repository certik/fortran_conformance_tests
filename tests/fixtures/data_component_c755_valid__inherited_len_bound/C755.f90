program p
implicit none
type :: parent(n)
    integer, len :: n
    integer :: first(n)
end type
type, extends(parent) :: child
    integer :: second(n+1)
end type
type(child(2)) :: value
value%first = [11,13]
value%second = [17,19,23]
if (size(value%first) /= 2 .or. size(value%second) /= 3) error stop 1
if (any(value%first /= [11,13])) error stop 2
if (any(value%second /= [17,19,23])) error stop 3
end program
