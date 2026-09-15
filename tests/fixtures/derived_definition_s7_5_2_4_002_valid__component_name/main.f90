program p
use types_a, only: a_record => record
use types_b, only: b_record => record
use dispatch, only: identify
use iso_c_binding, only: c_int
implicit none
type(a_record) :: a
type(b_record) :: b
a%x=11
a%y=13
b%x=17
b%z=19
if (identify(a) /= 1) error stop 1
if (identify(b) /= 2) error stop 2
end program
