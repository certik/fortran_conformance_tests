program p
implicit none
type :: record
    integer, pointer, contiguous :: field(:)
end type
type(record) :: value
integer, target :: target(2)
target = [11,13]
nullify(value%field)
if (associated(value%field)) error stop 1
value%field => target
if (.not. associated(value%field)) error stop 2
if (.not. is_contiguous(value%field)) error stop 3
if (any(value%field /= [11,13])) error stop 4
value%field(2) = 17
if (any(target /= [11,17])) error stop 5
nullify(value%field)
end program
