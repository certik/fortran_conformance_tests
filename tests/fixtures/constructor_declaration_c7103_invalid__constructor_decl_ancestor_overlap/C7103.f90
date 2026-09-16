module constructor_types
implicit none
type :: parent
integer :: x
integer :: y
end type parent
type, extends(parent) :: child
integer :: z
end type child
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(parent) :: parent_value
type(child) :: value
parent_value%x=11
parent_value%y=13
value=child(parent=parent_value,x=17,z=19)
end program constructor_case
