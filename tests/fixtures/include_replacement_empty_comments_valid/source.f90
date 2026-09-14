program inclusion
implicit none
integer :: value
value = 17
include 'empty.inc'
include 'comments.inc'
if (value /= 17) stop 1
end program inclusion
