program inclusion
implicit none
integer :: value
character(len=*), parameter :: part = 'payload.inc'
value = -9
include part
if (value /= 23) stop 1
end program inclusion
