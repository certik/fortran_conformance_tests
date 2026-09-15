program p
use types_a, only: caller_record => record
use worker, only: change
use iso_c_binding, only: c_int
implicit none
type(caller_record) :: value
value%code = 11
value%label = 'AB'
call change(value)
if (value%code /= 13 .or. value%label /= 'CD') error stop 2
end program
