! C801 (R801) The same attr-spec shall not appear more than once in a given
! type-declaration-stmt.
subroutine c801_allocatable()
    implicit none
    real, allocatable :: b(:)   ! {error C801 allocatable}
    allocate(b(2))
end subroutine

















