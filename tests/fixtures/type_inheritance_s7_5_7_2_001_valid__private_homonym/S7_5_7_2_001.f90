program p
use provider, only: set_hidden, get_hidden
use extension, only: child
implicit none
type(child) :: object
integer :: inherited_value
object%hidden = 9
call set_hidden(object, 7)
inherited_value = get_hidden(object)
if (inherited_value /= 7) error stop 1
if (object%hidden /= 9) error stop 2
end program
