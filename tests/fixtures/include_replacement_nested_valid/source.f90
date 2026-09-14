program inclusion
implicit none
integer :: value
value = 1
include 'outer.inc'
if (value /= 45) stop 1
end program inclusion
