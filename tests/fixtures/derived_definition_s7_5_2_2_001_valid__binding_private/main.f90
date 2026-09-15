program p
use provider, only: published, initialize, mutate_inside, check_inside, record
implicit none
type(record) :: local
call initialize()
if (check_inside() /= 11) error stop 1
if (published%payload /= 11) error stop 2
published%payload = 13
if (check_inside() /= 13) error stop 3
local%payload = 19
if (local%payload /= 19) error stop 6
end program
