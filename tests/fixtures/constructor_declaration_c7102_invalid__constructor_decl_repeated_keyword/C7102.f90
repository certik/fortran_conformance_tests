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
value=pair(left=11,right=11)
value=pair(left=11,left=13,right=17)
end program constructor_case
