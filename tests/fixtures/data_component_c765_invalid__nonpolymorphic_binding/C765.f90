module definitions
implicit none
type :: record
integer :: payload
contains
procedure :: action
end type
contains
subroutine action(self)
type(record), intent(in) :: self
end subroutine
end module
