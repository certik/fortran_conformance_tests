module definitions
implicit none
contains
subroutine outer(dummy)
integer, intent(in) :: dummy(:)
type :: record
    integer :: field(size(dummy))
end type
end subroutine
end module
