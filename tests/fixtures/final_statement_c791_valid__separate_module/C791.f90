module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish
end type record
interface
module subroutine finish(self)
type(record), intent(inout) :: self
end subroutine finish
end interface
end module final_defs
