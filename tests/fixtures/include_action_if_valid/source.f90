program inclusion
implicit none
integer :: value
value = -9
if (.true.) then
include 'payload.inc'
end if
if (value /= 23) stop 1
end program inclusion
