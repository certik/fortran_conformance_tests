module worker
use types_b, only: record
use iso_c_binding, only: c_int
implicit none
contains
subroutine change(value)
type(record), intent(inout) :: value
if (value%first /= 0_c_int .or. value%second /= 1_c_int) error stop 1
value%first = 1_c_int
value%second = 0_c_int
end subroutine
end module
