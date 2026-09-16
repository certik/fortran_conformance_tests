program p
use provider, only: published, initialize, inspect
implicit none
call initialize()
if (.not. associated(published%action)) error stop 2
if (published%action() /= 17) error stop 3
end program
