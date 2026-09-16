module provider
implicit none
private
public :: set_payload
type, public :: original
    integer, public :: payload
end type
contains
subroutine set_payload(item)
class(original), intent(inout) :: item
item%payload = 17
end subroutine
end module
