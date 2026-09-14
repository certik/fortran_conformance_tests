program inclusion
implicit none
integer :: value
value = -9
value = answer()
if (value /= 43) stop 1
contains
include 'procedure.inc'
end program inclusion
