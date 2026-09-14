program inclusion
implicit none
integer :: value
value = 0
include 'first.inc'
if (value /= 1) stop 1
end program inclusion
