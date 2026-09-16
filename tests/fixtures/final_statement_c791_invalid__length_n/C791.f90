module final_defs
implicit none
type :: record(n,m)
integer, len :: n,m
integer :: payload
contains
final :: finish
end type record
contains
subroutine finish(self)
type(record(2,*)), intent(inout) :: self
end subroutine finish
end module final_defs
