module tbp_provider
implicit none
type :: record
integer :: payload
contains
procedure :: specific => implementation
generic, public :: g => specific
end type record
type(record) :: object
contains
integer function implementation(self) result(value)
class(record), intent(in) :: self
value = self%payload
end function implementation
end module tbp_provider
