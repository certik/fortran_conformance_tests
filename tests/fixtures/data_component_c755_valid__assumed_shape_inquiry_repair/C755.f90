module definitions
implicit none
contains
subroutine outer(dummy)
integer, intent(in) :: dummy(:)
type :: record
    integer :: field(2)
end type
end subroutine
end module
