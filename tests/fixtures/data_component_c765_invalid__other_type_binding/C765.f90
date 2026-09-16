module definitions
implicit none
type :: other
integer :: payload
end type
type :: record
integer :: payload
contains
procedure :: action
end type
contains
subroutine action(self, witness)
class(other), intent(in) :: self
class(record), intent(in) :: witness
end subroutine
end module
