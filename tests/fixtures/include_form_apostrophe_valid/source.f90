program inclusion
implicit none
integer :: value
value = -9
INCLUDE 'payload.inc'
if (value /= 23) stop 1
end program inclusion
