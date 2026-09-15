program p
use types_a, only: a_record => record
use types_b, only: b_record => record
implicit none
type(a_record) :: a
type(b_record) :: b
a%payload = 11
b%payload = 13
if (same_type_as(a,b)) error stop 1
if (a%payload /= 11 .or. b%payload /= 13) error stop 2
end program
