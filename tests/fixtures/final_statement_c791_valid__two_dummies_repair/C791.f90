module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish
end type record
contains
subroutine finish(self)
type(record), intent(inout) :: self
integer :: spare
end subroutine finish
end module final_defs
