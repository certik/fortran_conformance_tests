program p
use root, only: inspect
implicit none
integer :: tag
call inspect(tag)
if (tag /= 17) error stop 1
end program
