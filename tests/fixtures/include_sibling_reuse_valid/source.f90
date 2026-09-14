program inclusion
implicit none
integer :: value
value = 0
include 'first.inc'
include 'second.inc'
if (value /= 3) stop 1
end program inclusion
