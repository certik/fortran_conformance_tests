module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish_scalar
final :: finish_vector
end type record
contains
subroutine finish_scalar(scalar)
type(record), intent(inout) :: scalar
end subroutine finish_scalar
subroutine finish_vector(vector)
type(record), intent(inout) :: vector(:)
end subroutine finish_vector
end module final_defs
