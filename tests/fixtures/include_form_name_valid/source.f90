program inclusion
implicit none
integer :: value
integer :: include
value = -9
include = 10
include 'payload.inc'
value = include
if (value /= 12) stop 1
end program inclusion
