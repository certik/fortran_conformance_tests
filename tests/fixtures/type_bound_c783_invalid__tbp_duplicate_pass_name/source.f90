module tbp_defs
implicit none
type :: record
contains
procedure, pass(self), pass(self) :: act => impl
end type record
contains
subroutine impl(self)
class(record), intent(in) :: self
end subroutine impl
end module tbp_defs
