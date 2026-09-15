module dispatch
implicit none
interface identify
module procedure left_tag, right_tag
end interface
contains
integer function left_tag(value) result(tag)
use types_a, only: record => record
use iso_c_binding, only: c_int
implicit none
type(record), intent(in) :: value
if (value%payload/=11) error stop 3
tag = 1
end function
integer function right_tag(value) result(tag)
use types_b, only: record => record
use iso_c_binding, only: c_int
implicit none
type(record), intent(in) :: value
if (any(value%payload/=[13,17])) error stop 4
tag = 2
end function
end module
