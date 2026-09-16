module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish
final :: finish ! repeated occurrence
end type record
contains
subroutine finish(self)
type(record), intent(inout) :: self
end subroutine finish
end module final_defs
