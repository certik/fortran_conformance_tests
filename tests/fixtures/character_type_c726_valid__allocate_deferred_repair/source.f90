































subroutine c726_allocate_dummy_not_assumed(d)
    implicit none
    character(:), allocatable, intent(out) :: d
    allocate(character(3) :: d)   ! {error C726 allocate-dummy-deferred}
end subroutine









