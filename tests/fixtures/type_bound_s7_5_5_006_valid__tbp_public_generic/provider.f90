module tbp_provider
implicit none
private
type, public :: record
private
integer :: payload
contains
private
procedure, private :: specific => implementation
generic, public :: get => specific
end type record
type(record), public :: object
public :: prepare
contains
subroutine prepare()
object%payload = 17
end subroutine prepare
integer function implementation(self) result(value)
class(record), intent(in) :: self
value = self%payload
end function implementation
end module tbp_provider
