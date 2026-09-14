program inclusion
implicit none
integer :: value
value = 0
include 'payload.inc'; include 'payload.inc'
if (value /= 2) stop 1
end program inclusion
