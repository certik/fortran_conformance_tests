program inclusion
implicit none
integer :: value
character(len=32) :: directive
value = -9
value = 0
directive = "#include 'payload.inc'"
! include 'payload.inc'
include 'payload.inc'
if (len_trim(directive) /= 22) stop 2
if (value /= 1) stop 1
end program inclusion
