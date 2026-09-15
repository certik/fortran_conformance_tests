module worker
use types_b, only: remote_record => record
use iso_c_binding, only: c_int
implicit none
contains
subroutine change(value)
type(remote_record), intent(inout) :: value
if (value%code /= 11 .or. value%label /= 'AB') error stop 1
value%code = 13
value%label = 'CD'
end subroutine
end module
