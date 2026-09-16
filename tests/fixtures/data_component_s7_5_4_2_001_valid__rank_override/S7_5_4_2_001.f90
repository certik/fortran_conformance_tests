program p
implicit none
type :: record
    integer, dimension(2,3) :: local(4), inherited
end type
type(record) :: value
value%local = [11,13,17,19]
value%inherited = 23
if (rank(value%local) /= 1 .or. size(value%local) /= 4) error stop 1
if (rank(value%inherited) /= 2) error stop 2
if (any(shape(value%inherited) /= [2,3])) error stop 3
if (any(value%local /= [11,13,17,19])) error stop 4
if (any(value%inherited /= 23)) error stop 5
end program
