module constructor_types
implicit none
type :: pair
integer :: left
integer :: right
end type pair
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(pair) :: value
value=pair(11,right=13)
value=pair(left=11,13)
end program constructor_case
