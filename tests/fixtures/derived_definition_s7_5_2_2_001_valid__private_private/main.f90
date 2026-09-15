program p
use provider, only: published, initialize, mutate_inside, check_inside
implicit none
call initialize()
if (check_inside() /= 11) error stop 1
call mutate_inside()
if (check_inside() /= 13) error stop 3
end program
