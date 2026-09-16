program p
implicit none
type :: record
    procedure(), pointer, nopass :: action
end type
type(record) :: value
external :: target
integer :: tag
tag = 0
nullify(value%action)
value%action => target
if (.not. associated(value%action)) error stop 1
call value%action(tag)
if (tag /= 17) error stop 2
end program
