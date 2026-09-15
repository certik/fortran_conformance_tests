program p
use provider, only: record
implicit none
type(record) :: value
value%payload = 11
if (value%payload /= 11) error stop 1
end program
