program p
implicit none
integer :: n
n = size([])
if (n /= 0) error stop 1
if (sum([integer ::]) /= 0) error stop 2
end program p
