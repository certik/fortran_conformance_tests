module constructor_types
implicit none
type :: holder
integer, pointer :: p
end type holder
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(holder) :: value
value=holder()
end program constructor_case
