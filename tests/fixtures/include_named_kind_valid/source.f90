program inclusion
implicit none
integer :: value
integer, parameter :: ck = kind('a')
value = -9
include 'payload.inc'
if (value /= 23) stop 1
end program inclusion
