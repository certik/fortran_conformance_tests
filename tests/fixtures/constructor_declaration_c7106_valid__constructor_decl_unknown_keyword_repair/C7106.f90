module constructor_types
implicit none
type :: packet
integer :: payload
end type packet
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(packet) :: value
value=packet(payload=17)
end program constructor_case
