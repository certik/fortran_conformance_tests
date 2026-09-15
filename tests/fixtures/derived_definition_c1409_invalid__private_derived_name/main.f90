program p
use provider, only: hidden_record
implicit none
type(hidden_record) :: value
value = hidden_record(17)
if (value%payload /= 17) error stop 1
end program
