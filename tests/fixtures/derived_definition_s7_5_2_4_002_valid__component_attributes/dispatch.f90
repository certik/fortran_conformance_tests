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
if (.not. associated(value%payload)) error stop 3
if (size(value%payload)/=2) error stop 4
if (any(value%payload/=[11,13])) error stop 5
tag = 1
end function
integer function right_tag(value) result(tag)
use types_b, only: record => record
use iso_c_binding, only: c_int
implicit none
type(record), intent(in) :: value
if (.not. allocated(value%payload)) error stop 3
if (size(value%payload)/=2) error stop 4
if (any(value%payload/=[17,19])) error stop 5
tag = 2
end function
end module
