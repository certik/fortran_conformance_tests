program p
implicit none
type :: leaf
integer :: field
end type
type :: record
    type(leaf) :: child
end type
type(record) :: value
value%child%field = 13
if (value%child%field /= 13) error stop 1
end program
