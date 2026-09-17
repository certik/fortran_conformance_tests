! C815 An entity shall not be explicitly given any attribute more than once
! in a scoping unit.  (Distinct from C801: the attribute is repeated across
! statements, not within one type-declaration-stmt.)
subroutine c815_allocatable_stmt()
    implicit none
    integer, allocatable :: b(:)
       ! {error C815 allocatable-stmt}
    allocate(b(2))
end subroutine






















