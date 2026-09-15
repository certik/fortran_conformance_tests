module dispatch
implicit none
interface identify
module procedure left_tag, right_tag
end interface
contains
integer function left_tag(value) result(tag)
use types_a, only: left_record => record
use iso_c_binding, only: c_int
implicit none
type(left_record), intent(in) :: value
tag = 1
end function
integer function right_tag(value) result(tag)
use types_b, only: right_record => record
use iso_c_binding, only: c_int
implicit none
type(right_record), intent(in) :: value
tag = 2
end function
end module
