module constructor_types
implicit none
type :: prior
integer :: payload
end type prior
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(prior), parameter :: declared=prior(payload=17)

end program constructor_case
