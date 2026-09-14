program inclusion
implicit none
integer :: value
value = 1
include 'step.inc'
value = value * 3
include 'step.inc'
if (value /= 19) stop 1
end program inclusion
