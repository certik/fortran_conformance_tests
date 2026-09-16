module final_defs
implicit none
type :: record(k1,k2,n)
integer, kind :: k1,k2
integer, len :: n
integer :: payload
contains
final :: finish_first, finish_second
end type record
contains
subroutine finish_first(first)
type(record(1,2,*)), intent(inout) :: first
end subroutine finish_first
subroutine finish_second(second)
type(record(1,2,*)), intent(inout) :: second
end subroutine finish_second
end module final_defs
