program inclusion
implicit none
integer :: value
value = -9
  include   'payload.inc'   ! trailing comment &
if (value /= 23) stop 1
end program inclusion
