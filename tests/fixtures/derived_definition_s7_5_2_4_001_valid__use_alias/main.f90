program p
use types, only: caller_record => record
use worker, only: change
implicit none
type(caller_record) :: value
value%payload = 11
call change(value)
if (value%payload /= 17) error stop 3
end program
