module final_defs
implicit none
type :: record(k,n)
integer, kind :: k
integer, len :: n
integer :: payload
contains
final :: finish_any, finish_fixed
end type record
contains
subroutine finish_any(any_rank)
type(record(1,*)), intent(inout) :: any_rank(..)
end subroutine finish_any
subroutine finish_fixed(fixed)
type(record(2,*)), intent(inout) :: fixed
end subroutine finish_fixed
end module final_defs
