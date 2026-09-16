module tbp_provider
implicit none
type :: record
integer :: payload
contains
procedure, private :: secret => implementation
end type record
type(record) :: object
interface
module subroutine inspect()
end subroutine inspect
end interface
contains
integer function implementation(self) result(value)
class(record), intent(in) :: self
value = self%payload
end function implementation
end module tbp_provider
