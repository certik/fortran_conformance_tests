module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish_any
end type record
contains
subroutine finish_any(any_rank)
type(record), intent(inout) :: any_rank(..)
end subroutine finish_any
end module final_defs
