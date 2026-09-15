module provider
implicit none
private
public :: published, initialize, mutate_inside, check_inside
type, public :: record
    integer :: payload
contains
    private
    procedure :: get_value, set_value
end type
type(record) :: published
contains
subroutine initialize()
published%payload = 11
end subroutine
subroutine mutate_inside()
call published%set_value(13)
end subroutine
integer function check_inside()
check_inside = published%get_value()
end function
integer function get_value(self)
class(record), intent(in) :: self
get_value = self%payload
end function
subroutine set_value(self, number)
class(record), intent(inout) :: self
integer, intent(in) :: number
self%payload = number
end subroutine
end module
