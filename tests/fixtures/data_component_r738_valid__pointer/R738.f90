program p
implicit none
type :: record
    integer, pointer :: field
end type
type(record) :: value
integer, target :: target
target = 11
nullify(value%field)
if (associated(value%field)) error stop 1
value%field => target
if (.not. associated(value%field)) error stop 2
if (value%field /= 11) error stop 3
value%field = 13
if (target /= 13) error stop 4
nullify(value%field)
end program
