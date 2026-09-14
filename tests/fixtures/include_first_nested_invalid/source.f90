program inclusion
implicit none
integer :: value
value = -9
value = 10 &
include 'outer.inc'
if (value /= 12) stop 1
end program inclusion
