module constructor_types
implicit none
type :: empty
end type empty
type :: defaulted
integer :: payload=11
end type defaulted
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(empty) :: a
type(defaulted) :: b
a=empty()
b=defaulted()
end program constructor_case
