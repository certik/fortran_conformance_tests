module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish_external
end type record
interface
subroutine finish_external(self)
import :: record
type(record), intent(inout) :: self
end subroutine finish_external
end interface
contains
subroutine finish_module(self)
type(record), intent(inout) :: self
end subroutine finish_module
end module final_defs
subroutine finish_external(self)
use final_defs, only: record
implicit none
type(record), intent(inout) :: self
end subroutine finish_external
