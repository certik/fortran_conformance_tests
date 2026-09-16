module tbp_provider
implicit none
type :: parent
integer :: payload
contains
procedure, private :: secret => implementation
end type parent
contains
integer function implementation(self) result(value)
class(parent), intent(in) :: self
value = self%payload
end function implementation
end module tbp_provider
