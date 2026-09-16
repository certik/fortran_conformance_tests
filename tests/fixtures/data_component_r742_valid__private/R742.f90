program p
use provider, only: published, initialize, inspect
implicit none
call initialize()
if (inspect() /= 17) error stop 2
end program
