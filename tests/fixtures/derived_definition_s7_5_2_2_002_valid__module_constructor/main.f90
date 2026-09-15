program p
use provider, only: inspect
implicit none
if (inspect() /= 17) error stop 1
end program
