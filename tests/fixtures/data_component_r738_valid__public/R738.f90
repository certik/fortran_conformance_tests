program p
use provider, only: published, initialize, inspect
implicit none
call initialize()
if (published%field /= 11) error stop 1
end program
