module final_defs
implicit none
type :: record
integer :: payload
contains
final :: finish_ordinary, finish_elemental
end type record
contains
subroutine finish_ordinary(ordinary)
type(record), intent(inout) :: ordinary
end subroutine finish_ordinary
impure elemental subroutine finish_elemental(element)
type(record), intent(inout) :: element
end subroutine finish_elemental
end module final_defs
