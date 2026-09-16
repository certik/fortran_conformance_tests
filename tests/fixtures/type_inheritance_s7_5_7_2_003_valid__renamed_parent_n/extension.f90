module extension
use provider, only: alias => original, set_payload
implicit none
private
private :: alias
public :: child, object, initialize
type, extends(alias) :: child
    private
    integer :: marker
end type
type(child) :: object
contains
subroutine initialize()
object%marker = 41
call set_payload(object)
end subroutine
end module
