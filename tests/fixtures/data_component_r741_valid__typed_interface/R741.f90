program p
implicit none
type :: record
    procedure(integer), pointer, nopass :: action
end type
type(record) :: value
integer, external :: target
nullify(value%action)
value%action => target
if (.not. associated(value%action)) error stop 1
if (value%action() /= 17) error stop 2
end program
