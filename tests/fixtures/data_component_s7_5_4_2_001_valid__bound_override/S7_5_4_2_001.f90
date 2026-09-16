program p
implicit none
type :: record
    integer, dimension(-1:1) :: local(2:4), inherited
end type
type(record) :: value
value%local = [11,13,17]
value%inherited = [19,23,29]
if (rank(value%local) /= 1 .or. rank(value%inherited) /= 1) error stop 1
if (size(value%local) /= 3 .or. size(value%inherited) /= 3) error stop 2
if (lbound(value%local,1) /= 2 .or. ubound(value%local,1) /= 4) error stop 3
if (lbound(value%inherited,1) /= -1 .or. ubound(value%inherited,1) /= 1) error stop 4
if (any(value%local /= [11,13,17])) error stop 5
if (any(value%inherited /= [19,23,29])) error stop 6
end program
