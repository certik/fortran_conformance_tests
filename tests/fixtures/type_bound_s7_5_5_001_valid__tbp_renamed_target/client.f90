program p
use tbp_consumer, only: record
implicit none
type(record) :: item
integer :: observed
item%payload = 11
observed = item%local_name()
if (observed /= 22) error stop 1
observed = item%explicit_alias()
if (observed /= 22) error stop 2
if (item%payload /= 11) error stop 3
end program p
