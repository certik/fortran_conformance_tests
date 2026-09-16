program p
implicit none
type :: parent
    integer :: payload
end type
type, extends(parent) :: child
    integer :: marker
end type
type(child) :: object
integer :: observed
object%payload = 17
object%marker = 41
if (rank(object%parent) /= 0) error stop 1
observed = parent_payload(object%parent)
if (observed /= 17) error stop 2
if (object%marker /= 41) error stop 3
contains
integer function parent_payload(item) result(value)
type(parent), intent(in) :: item
value = item%payload
end function
end program p
