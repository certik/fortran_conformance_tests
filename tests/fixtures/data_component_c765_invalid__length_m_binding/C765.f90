module definitions
implicit none
type :: record(n,m)
integer, len :: n,m
character(n) :: label
integer :: values(m)
contains
procedure :: action
end type
contains
subroutine action(self)
class(record(*,3)), intent(in) :: self
end subroutine
end module
