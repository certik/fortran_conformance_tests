module provider
implicit none
private
public :: parent, set_hidden, get_hidden
type :: parent
    private
    integer :: hidden
end type
contains
subroutine set_hidden(object, number)
class(parent), intent(inout) :: object
integer, intent(in) :: number
object%hidden = number
end subroutine
integer function get_hidden(object) result(number)
class(parent), intent(in) :: object
number = object%hidden
end function
end module
