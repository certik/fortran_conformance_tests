program p
implicit none
type :: parent
    integer :: value
end type
type, extends(parent) :: child
    integer :: marker
end type
type(child) :: object
object%value = 3
object%marker = 41
if (object%parent%value /= 3) error stop 1
object%parent%value = 7
if (object%value /= 7) error stop 2
if (object%marker /= 41) error stop 3
object%value = 11
if (object%parent%value /= 11) error stop 4
if (object%marker /= 41) error stop 5
end program p
