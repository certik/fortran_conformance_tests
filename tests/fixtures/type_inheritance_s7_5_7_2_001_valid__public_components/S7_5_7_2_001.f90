program p
implicit none
type :: parent
    integer :: left, right
end type
type, extends(parent) :: child
    integer :: marker
end type
type(child) :: object
object%left = 3
object%right = 7
object%marker = 41
if (object%left /= 3) error stop 1
if (object%right /= 7) error stop 2
if (object%marker /= 41) error stop 3
end program p
