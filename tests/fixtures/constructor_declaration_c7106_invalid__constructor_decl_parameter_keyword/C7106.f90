module constructor_types
implicit none
type :: packet(k)
integer, kind :: k
integer :: payload
end type packet
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(packet(k=2)) :: value
value=packet(k=2)(payload=17,k=3)
end program constructor_case
