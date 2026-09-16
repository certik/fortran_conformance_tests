module tbp_defs
implicit none
type :: record
contains
procedure :: op => op_impl
generic :: operator(.probe.) => op
end type record
contains
integer function op_impl(self) result(value)
class(record), intent(in) :: self
value = 17
end function op_impl
end module tbp_defs
