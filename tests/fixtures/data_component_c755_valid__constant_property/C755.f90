program p
implicit none
integer :: prototype(3)
type :: record
    integer :: field(size(prototype))
end type
type(record) :: value
value%field = [11,13,17]
if (size(value%field) /= 3) error stop 1
if (any(value%field /= [11,13,17])) error stop 2
end program
