program p
use provider, only: published, initialize, mutate_inside, check_inside, record
implicit none
type(record) :: local
call initialize()
if (check_inside() /= 11) error stop 1
call mutate_inside()
if (check_inside() /= 13) error stop 3
if (published%get_value() /= 13) error stop 4
call published%set_value(17)
if (check_inside() /= 17) error stop 5
call local%set_value(19)
if (local%get_value() /= 19) error stop 6
end program
