module final_defs
implicit none
type :: other
integer :: payload
end type other
type :: record
integer :: payload
contains
final :: finish
end type record
contains
subroutine finish(self)
type(other), intent(inout) :: self
end subroutine finish
end module final_defs
