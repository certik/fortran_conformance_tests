program p
use provider, only: published, initialize, mutate_inside, check_inside
implicit none
call initialize()
if (check_inside() /= 11) error stop 1
if (published%payload /= 11) error stop 2
published%payload = 13
if (check_inside() /= 13) error stop 3
if (published%get_value() /= 13) error stop 4
call published%set_value(17)
if (check_inside() /= 17) error stop 5
end program
