module definitions
implicit none
type :: record
integer :: payload
contains
procedure :: action
end type
contains
subroutine action(self)
class(record), value, intent(in) :: self
end subroutine
end module
