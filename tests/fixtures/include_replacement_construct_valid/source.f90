program inclusion
implicit none
integer :: value
value = 5
include 'open.inc'
end if
if (value /= 7) stop 1
end program inclusion
