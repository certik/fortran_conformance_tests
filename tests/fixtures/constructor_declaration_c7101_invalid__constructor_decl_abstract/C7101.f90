module constructor_types
implicit none
type, abstract :: base
integer :: payload
end type base
contains
subroutine observe(self)
class(base), intent(in) :: self
end subroutine observe
end module constructor_types
program constructor_case
use constructor_types
implicit none

call observe(base(payload=17))
end program constructor_case
