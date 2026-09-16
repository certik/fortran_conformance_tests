module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish_first, finish_second
end type record
contains
subroutine finish_first(first)
type(record), intent(inout) :: first
end subroutine finish_first
subroutine finish_second(second)
type(record), intent(inout) :: second
end subroutine finish_second
end module final_defs
