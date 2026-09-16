module tbp_defs
implicit none
type :: record
contains
procedure, pass :: with_self => impl
procedure, nopass :: without_self => other
end type record
contains
subroutine impl(self)
class(record), intent(in) :: self
end subroutine impl
subroutine other()
end subroutine other
end module tbp_defs
