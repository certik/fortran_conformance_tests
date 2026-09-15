subroutine p(assumed_dummy)
    implicit none
    character(*), allocatable, intent(inout) :: assumed_dummy
    character(:), allocatable :: local_deferred
    allocate(character(*) :: assumed_dummy,local_deferred)
end subroutine
