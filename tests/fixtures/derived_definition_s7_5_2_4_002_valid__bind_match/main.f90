program p
use types_a, only: record
use worker, only: change
use iso_c_binding, only: c_int
implicit none
type(record) :: value
value%first = 0_c_int
value%second = 1_c_int
call change(value)
if (value%first /= 1_c_int .or. value%second /= 0_c_int) error stop 2
end program
